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
#
# This script generates Kotlin dictionaries for drawable resources from PNG files. 
# The resulting content are supposed to be copied into the Android project. 
# The PNG files have to be imported into the Android project as drawable resources.

import os
import shutil

# Get the script path
script_path = os.path.dirname(os.path.realpath(__file__))
smartwatch_experiment_folder = os.path.join(script_path, 'output', 'smartwatch-export')

files_path = os.path.join(script_path, "files.txt")
int_file_path = os.path.join(script_path, "to_int.txt")
word_file_path = os.path.join(script_path, "to_R_drawable.txt")
kotlin_file_path = os.path.join(script_path, "copy_to_kotlin.txt")

# Open the files
files = open(files_path, "w")
int_file = open(int_file_path, "w")
word_file = open(word_file_path, "w")

counter = 0
for file in os.listdir(smartwatch_experiment_folder):
    if file.endswith(".png") and (file.startswith("experiment_right_fr") or file.startswith("training_right_fr")):
        filename = file.replace("-", "_").lower().replace(".png", "")
        
        files.write(f'{filename},\n')
        int_file.write(f'{counter} to "{filename}",\n')
        word_file.write(f'"{filename}" to R.drawable.{filename},\n')
        counter += 1

blank_file_path = os.path.join(script_path, "blank.png")
no_help_file_path = os.path.join(script_path, "no_help_available.png")
# Copy the blank and no_help_available_files to the smartwatch experiment folder
shutil.copy(blank_file_path, smartwatch_experiment_folder)
shutil.copy(no_help_file_path, smartwatch_experiment_folder)

files.write('blank,\n')
files.write('no_help_available,\n')
int_file.write(f'{counter} to "blank",\n')
int_file.write(f'{counter + 1} to "no_help_available",\n')
word_file.write('"blank" to R.drawable.blank,\n')
word_file.write('"no_help_available" to R.drawable.no_help_available,\n')
        
# Remove trailing ',\n'
files.seek(files.tell() - 2, os.SEEK_SET)
files.truncate()
int_file.seek(int_file.tell() - 2, os.SEEK_SET)
int_file.truncate()
word_file.seek(word_file.tell() - 2, os.SEEK_SET)
word_file.truncate()

files.close()
int_file.close()
word_file.close()

kotlin_file = open(kotlin_file_path, "w")
kotlin_file.write('// Create a list of images\n')
kotlin_file.write('val intDrawables = mapOf(\n')
for line in open(int_file_path, "r"):
    kotlin_file.write(f'\t{line}')
kotlin_file.write('\n)\n\n')

# Same for below code

kotlin_file.write('val drawableIds = mapOf(\n')
for line in open(word_file_path, "r"):
    kotlin_file.write(f'\t{line}')
kotlin_file.write('\n)\n')

kotlin_file.close()

# Delete the files
os.remove(os.path.join(script_path, "files.txt"))
os.remove(os.path.join(script_path, "to_int.txt"))
os.remove(os.path.join(script_path, "to_R_drawable.txt"))