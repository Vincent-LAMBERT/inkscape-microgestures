#! /usr/bin/env python3

import os
import shutil
import sys

from microrep.map_commands import MapCommands

script_path = os.path.dirname(os.path.realpath(__file__))
base_file = os.path.join(script_path, 'initial.svg')
config_file = os.path.join(script_path, 'config.csv')
output_folder = os.path.join(script_path, 'output')
icons_folder = os.path.join(script_path, 'icons')
COMMAND_RADIUS = 2.5 # Default radius for commands

def deleteFolderContent(folder):
    """
    Delete the content of a folder
    """
    for element in os.listdir(folder):
        # If it's a folder, delete it 
        if os.path.isdir(os.path.join(folder, element)):
            shutil.rmtree(os.path.join(folder, element))
        elif os.path.isfile(os.path.join(folder, element)):
            os.remove(os.path.join(folder, element))


def map_commands(file, output_folder, config_file, icons_folder, showMg=False):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    icons_str = f"--icons={icons_folder}"
    showMg_str = f"--showMg={showMg}"
    radius_str = f"--radius={COMMAND_RADIUS}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = MapCommands()
    export_rep.run(args=[file, path_str, config_str, icons_str, radius_str, showMg_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__
        
if __name__== "__main__":
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # Delete the content of the output folder
    deleteFolderContent(output_folder)
    
    print(f"Mapping commands for {base_file}")
    # Create the output for the given representation  
    map_commands(base_file, output_folder, config_file, icons_folder)