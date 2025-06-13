#! /usr/bin/env python3

import os
import shutil
import sys

from microrep.export_hand_poses import ExportHandPoses

script_path = os.path.dirname(os.path.realpath(__file__))
base_file = os.path.join(script_path, 'initial.svg')
config_file = os.path.join(script_path, 'config.csv')
output_folder = os.path.join(script_path, 'output')
FAMILY = 'MaS'

def deleteFolderContent(folder):
    for element in os.listdir(folder):
        # If it's a folder, delete it 
        if os.path.isdir(os.path.join(folder, element)):
            shutil.rmtree(os.path.join(folder, element))
        elif os.path.isfile(os.path.join(folder, element)):
            os.remove(os.path.join(folder, element))

def create_hand_poses(file, output_folder, config_file):
    """
    Create the hand poses for the given hand pose file.
    
    :param file: The hand pose file to create hand poses for.
    :param output_folder: The folder to save the hand poses in.
    :param config_dict: The configuration dictionary for the hand poses.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = ExportHandPoses()
    export_rep.run(args=[file, path_str, config_str])
    
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
    
    print(f"Creating hand poses for {base_file}")
    # Create the output for the given hand pose  
    create_hand_poses(base_file, output_folder, config_file)