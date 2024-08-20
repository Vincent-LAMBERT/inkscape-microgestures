#! /usr/bin/env python3
#######################################################################################################################
#  Copyright (c) 2023 Vincent LAMBERT
#  License: MIT
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
#######################################################################################################################
# NOTES
#
# Developing extensions:
#   SEE: https://inkscape.org/develop/extensions/
#   SEE: https://wiki.inkscape.org/wiki/Python_modules_for_extensions
#   SEE: https://wiki.inkscape.org/wiki/Using_the_Command_Line
#
# Implementation References:
#   SEE: https://github.com/nshkurkin/inkscape-export-layer-combos

import itertools
import csv
import os
import random
import logging
import sys

import microrep.core.utils as u

#######################################################################################################################

def compute_wanted_mappings(finger, microgestures=u.MICROGESTURES, fmcs=u.MICROGESTURE_CHARACTERISTICS, commands=u.COMMANDS) :
    """
    Return the wanted mappings.
    By default, returns every command that
    can be done with a microgesture in an dictionnary with the form
    [((finger1, microgesture1, characteristic1), command1), ((finger2, microgesture2, characteristic2), command2), ...]
    """
    wanted_mappings = []
    
    for microgesture in microgestures :
        for characteristic in fmcs[microgesture] :
            for command in commands :
                wanted_mappings.append(((finger, microgesture, characteristic), command))
    
    return wanted_mappings

def compute_combis(mcs, commands) :
    """
    Return a subset of the command combinations corresponding to the given list
    """
    command_combi = [p for p in itertools.combinations(commands, len(mcs))]
    
    combis = []
    for combi in command_combi :
        random_ordered_combi = random.sample(combi, len(combi))
        new_combi = list(zip(mcs, random_ordered_combi))
        combis.append(new_combi) # Tests at least once each command combination but not every mapping of theses combinations, only one random mapping (reduces by a factor of fact(len(fmcs)) the number of mappings!)
    
    # Keep 10 combinations in combis
    return combis[:5]
    
def compute_all_mappings(finger, category) :
    """
    Return all the command mappings corresponding to the given list
    """
    fmcs = []
    commands = []
    
    mappings = compute_wanted_mappings(finger, microgestures=[u.TAP, u.SWIPE], commands=category)

    for fmc, command in mappings:
        if fmc not in fmcs:
            fmcs.append(fmc)
        if command not in commands:
            commands.append(command)
            
    return compute_combis(fmcs, commands)

def compute_mappings_for_categories(categories) :
    """
    Compute the mappings for the given categories
    """
    all_mappings = []
    fingers = [u.INDEX]
    category_combinations = [p for p in itertools.combinations(categories, len(fingers))]
    for category_combi in category_combinations :
        combi_mappings = []
        for finger, category in zip(fingers, category_combi) :
            mappings = compute_all_mappings(finger, category)
            if len(combi_mappings) == 0 :
                combi_mappings = mappings
            else :
                all = combi_mappings
                combi_mappings = [x + y for x,y in zip(all, mappings)]
        all_mappings+=combi_mappings
            
    return all_mappings

def get_mapping_name(mapping) :
    """
    Return a name to describe the given mapping
    of the form [((finger1, microgesture1, characteristic1), command1), 
    (finger2, microgesture2, characteristic2), command2), ...]}
    """
    name = ""
    for fms, command in mapping:
        name += f"{fms[0][0].lower()}{fms[1][0].upper()}{fms[2][0].lower()}~{command}-"
    return name[:-1]

def get_mapping_commands(mapping, logit=logging.info) :
    """
    Return the commands corresponding to the given mapping
    of the form [((finger1, microgesture1, characteristic1), command1), 
    (finger2, microgesture2, characteristic2), command2), ...]}
    """
    commands = []
    for fmc, command in mapping:
        commands.append(command)
    return commands

def compute_default_mappings() :
    """
    Return the command mappings corresponding to the default configuration
    """
    return compute_mappings_for_categories(u.DEFAULT_CATEGORIES)
    # return [[(("tap", "tip"), "banana"), (("tap", "middle"), "watermelon"), (("tap", "base"), "blackberry"), (("swipe", "up"), "kiwi"), (("swipe", "down"), "plum")], [(("tap", "tip"), "pineapple"), (("tap", "middle"), "blackberry"), (("tap", "base"), "cherry"), (("swipe", "up"), "plum"), (("swipe", "down"), "banana")], [(("tap", "tip"), "cherry"), (("tap", "middle"), "pineapple"), (("tap", "base"), "blackberry"), (("swipe", "up"), "watermelon"), (("swipe", "down"), "kiwi")], [(("tap", "tip"), "kiwi"), (("tap", "middle"), "cherry"), (("tap", "base"), "watermelon"), (("swipe", "up"), "banana"), (("swipe", "down"), "plum")], [(("tap", "tip"), "blackberry"), (("tap", "middle"), "watermelon"), (("tap", "base"), "plum"), (("swipe", "up"), "pineapple"), (("swipe", "down"), "kiwi")], [(("tap", "tip"), "plum"), (("tap", "middle"), "blackberry"), (("tap", "base"), "banana"), (("swipe", "up"), "watermelon"), (("swipe", "down"), "cherry")], [(("tap", "tip"), "watermelon"), (("tap", "middle"), "plum"), (("tap", "base"), "blackberry"), (("swipe", "up"), "kiwi"), (("swipe", "down"), "cherry")]]

def get_mappings(file_path, logit=logging.info) :
    """
    Return the command mappings corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_mappings()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_mappings_from_file(file_path, logit)

def get_mappings_from_file(file_path, logit=logging.info) :
    """
    Return the command mappings corresponding to the given configuration file
    """
    mappings = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            combination = []
            for mg_command in row:
                finger, mcc = mg_command.split('+')
                mg, cc = mcc.split('_')
                charac, command = cc.split('-')
                combination.append(((finger, mg, charac), command))
            mappings.append(combination)
            
    return mappings

#######################################################################################################################

def create_configuration_file(mappings, file_path="./configuration/config_export_mapping_rep.csv") :
    """
    Creates the configuration file for the mappings
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))     
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in mappings:
            row = ["{0}+{1}_{2}-{3}".format(fmc[0], fmc[1], fmc[2], command) for fmc, command in combination]
            print(row)
            writer.writerow(row)
            
    # Creates the shortened version -> For export to pilot website
    file_path = file_path[:-4] + "_short.csv"
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))     
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in mappings:
            row = ["{0}{1}{2}~{3}".format(fmc[0][0].lower(), fmc[1][0].upper(), fmc[2][0].lower(), command.lower()) for fmc, command in combination]
            print(row)
            writer.writerow(row)

#######################################################################################################################

def _main():
    mappings = compute_default_mappings()
    if len(sys.argv) > 1 :
        create_configuration_file(mappings, sys.argv[1])
    else :
        create_configuration_file(mappings)

if __name__ == "__main__":
    _main()

#######################################################################################################################