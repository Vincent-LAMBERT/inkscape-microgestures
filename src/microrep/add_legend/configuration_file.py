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
#  AUTHORS OR COPYRIGHT u.HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
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
import random
import sys

import microrep.core.utils as u

#######################################################################################################################

def compute_default_legends() :
    """
    Return the command legends corresponding to the default configuration
    """
    return [[[(u.INDEX, u.TAP, u.TIP), (u.INDEX, u.HOLD, u.TIP)], [(u.INDEX, u.TAP, u.MIDDLE), (u.INDEX, u.HOLD, u.MIDDLE)], [(u.INDEX, u.TAP, u.BASE), (u.INDEX, u.HOLD, u.BASE)]], [[(u.INDEX, u.TAP, u.TIP)], [(u.INDEX, u.SWIPE, u.UP), (u.INDEX, u.TAP, u.MIDDLE), (u.INDEX, u.SWIPE, u.DOWN)], [(u.INDEX, u.TAP, u.BASE)]]]

def get_legends(file_path, logit=logging.info) :
    """
    Return the command legends corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_legends()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_legends_from_file(file_path, logit)

def get_legends_from_file(file_path, logit=logging.info) :
    """
    Return the command legends corresponding to the given configuration file
    """
    legends = []
    with open(file_path, 'r') as csvfile:
        for row in csvfile:
            row = [row.replace('\n', '')]
            legended_elements = row[0].split('_')
            legend = []
            for legended in legended_elements :
                fm, charac = legended.split('-')
                finger, mg = fm.split('+')
                charac = charac.replace('\n', '') # Just in case
                legend.append((finger, mg, charac))
            legends.append(legend)
    
    return legends

#######################################################################################################################

def create_configuration_file(legends, file_path="./configuration/config_export_legend_rep.csv") :
    """
    Creates the configuration file for the legends
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))     
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in legends:
            row = []
            for legend in combination:
                legended = ["{0}+{1}-{2}".format(finger, mg, charac) for (finger, mg, charac) in legend]
                row.append("_".join(legended))
            print(row)
            writer.writerow(row)

#######################################################################################################################

def _main():
    legends = compute_default_legends()
    if len(sys.argv) > 1 :
        create_configuration_file(legends, sys.argv[1])
    else :
        create_configuration_file(legends)

if __name__ == "__main__":
    _main()

#######################################################################################################################