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
import logging
import sys
import re

import microrep.core.utils as u

#######################################################################################################################

def compute_wanted_styles() :
    """
    Return the wanted styles.
    By default, returns every style that
    can be done with a finger in an dictionnary with the form
    [(microgesture1, style1, characteristic1), (microgesture2, style2, ...), ...]
    """
    wanted_styles = []
    
    for microgesture in u.MICROGESTURES :
        for style in u.STYLES :
            for characteristic in u.STYLE_CHARACTERISTICS[style] :
                wanted_styles.append((microgesture, style, characteristic))
    
    return wanted_styles

def compute_all_styles(style) :
    """
    Return all the styles combinations corresponding to the given list
    """
    combinations=[]
    for simultaneous_mg_nbr in range(1, len(style) + 1):
        for subset in itertools.combinations(style, simultaneous_mg_nbr):
            combinations.append(subset)
    return combinations

def style(style_name, combination) :
    """
    Return a style dictionnary of the form
    {'name': style_name, 'combination': [(microgesture1, style1, characteristic1), (microgesture2, style2, ...), ...]}
    """
    return {u.NAME: style_name, u.COMBINATION: combination}

def compute_default_styles() :
    """
    Return the style combinations corresponding to the default configuration
    """
    # Add color style
    default_color_style = [(u.TAP, u.FILL, u.COLORS[u.RED]), (u.TAP, u.STROKE, u.COLORS[u.RED]), (u.SWIPE, u.FILL, u.COLORS[u.BLUE]), (u.SWIPE, u.STROKE, u.COLORS[u.BLUE])]
    # Add size style
    default_size_style = [(u.TAP, u.STROKE_WIDTH, u.SIZES[u.THICK]), (u.SWIPE, u.PATH_SCALE, u.SIZES[u.THIN])]
    # Associate the styles
    combinations = [style('color', default_color_style), style('size', default_size_style)]
    return combinations

def get_mg_associated_styles(microgesture, combinations, logit=logging.info) :
    """
    The given combinations is an array of style combinations of the form
    [(microgesture1, style1, characteristic1), (microgesture2, style2, ...), ...]
    We return the styles associated to the given microgesture
    with a dictionary of the form 
    {style1: characteristic1, style2: characteristic2 ...}
    """
    style_combinations = dict()
    for combination in combinations :
        if combination[0] == microgesture :
            style_combinations[combination[1]] = combination[2]
    return style_combinations

def get_combinations(file_path, logit=logging.info) :
    """
    Return the style combinations corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_styles()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_combinations_from_file(file_path)

def get_combinations_from_file(file_path) :
    """
    Return the style combinations corresponding to the given configuration file
    """
    combinations = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            style, combi = row[0].split(' : ')
            combi_list = []
            for combi_tuple_str in combi.split('--'):
                # Get each element between the parenthesis that are separated by a comma
                elements = re.findall(r'\((.*?)\)', combi_tuple_str)[0]
                element_list = elements.split(', ')
                combi_list.append(tuple(element_list))
            combinations.append({u.NAME : style, u.COMBINATION: combi_list})
    return combinations

#######################################################################################################################

def create_configuration_file(combinations, file_path="./configuration/config_export_style_rep.csv") :
    """
    Creates the configuration file for the styles
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))      
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in combinations:   
            name = combination[u.NAME]
            styles = [str(style) for style in combination[u.COMBINATION]]
            combi = '--'.join(styles)
            combi = combi.replace("'", "")
            row = ["{0} : {1}".format(name, combi)]
            print(row)
            writer.writerow(row)

#######################################################################################################################

def _main():
    combinations = compute_default_styles()
    if len(sys.argv) > 1 :
        create_configuration_file(combinations, sys.argv[1])
    else :
        create_configuration_file(combinations)

if __name__ == "__main__":
    _main()

#######################################################################################################################