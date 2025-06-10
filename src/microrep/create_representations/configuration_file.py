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

import csv
import itertools
import logging
import os
import sys

import microrep.core.utils as u

#######################################################################################################################

def compute_wanted_microgestures() :
    """
    Return the wanted microgestures.
    By default, returns every microgesture that
    can be done with a finger in an array with the form
    [(microgesture1, characteristic1), (microgesture2, ...), ...]
    """
    wanted_microgestures = []
    
    for finger in u.FINGERS :
        for microgesture in u.MICROGESTURES :
            for characteristic in u.MICROGESTURE_CHARACTERISTICS[microgesture] :
                wanted_microgestures.append((finger, microgesture, characteristic))
    
    return wanted_microgestures

def compute_all_microgesture_combinations(microgestures) :
    """
    Return all the microgesture combinations corresponding to the given list
    """
    combinations=[]
    for simultaneous_mg_nbr in range(1, len(microgestures) + 1):
        for subset in itertools.combinations(microgestures, simultaneous_mg_nbr):
            combinations.append(subset)
    return combinations

def compute_default_microgesture_combinations() :
    """
    Return the microgesture combinations corresponding to the default configuration
    """
    ## Add swipes combination
    swipe_mg = [(u.INDEX, u.SWIPE, charac) for charac in u.MICROGESTURE_CHARACTERISTICS[u.SWIPE]]
    ## Add taps combination
    tap_mg = [(u.INDEX, u.TAP, charac) for charac in u.MICROGESTURE_CHARACTERISTICS[u.TAP]]
    ## Add the combination of taps, swipes and flexes
    combinations = [swipe_mg] + [tap_mg] + [x for x in [swipe_mg + tap_mg]]
    
    return combinations

def get_combinations(file_path, logit=logging.info) :
    """
    Return the microgesture combinations corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_microgesture_combinations()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_combinations_from_file(file_path)

def get_combinations_from_file(file_path) :
    """
    Return the microgesture combinations corresponding to the given configuration file
    """
    combinations = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            combi = get_combination_from_row(row)
            combinations.append(combi)          
    return combinations

def get_combination_from_row(row) :  
    combination = []
    for fmc in row:
        finger, mc = fmc.split('+')
        microgesture, characteristic = mc.split('-')
        combination.append((finger, microgesture, characteristic))
    return combination

#######################################################################################################################

def create_configuration_file(combinations, file_path="./configuration/config_export_mg_rep.csv") :
    """
    Creates the configuration file for the microgestures
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))            
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in combinations:
            row = ["{0}+{1}-{2}".format(finger, microgesture, characteristic) for finger, microgesture, characteristic in combination]
            print(row)
            writer.writerow(row)

#######################################################################################################################

def _main():
    combinations = compute_default_microgesture_combinations()
    if len(sys.argv) > 1 :
        create_configuration_file(combinations, sys.argv[1])
    else :
        create_configuration_file(combinations)

if __name__ == "__main__":
    _main()

#######################################################################################################################