#! /usr/bin/env python3

import os
import shutil
import sys

from microrep.add_overlap_adaptation import AddOverlapAdaptation

script_path = os.path.dirname(os.path.realpath(__file__))
base_file = os.path.join(script_path, 'initial.svg')
config_file = os.path.join(script_path, 'config.csv')
output_folder = os.path.join(script_path, 'output')

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

def add_overlap_adaptation(file, output_folder, prefix, strategy, integration):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    prefix_str = f"--prefix={prefix}"
    strategy_str = f"--strategy={strategy}"
    integration_str = f"--integration={integration}"
    
    # Redirect stdout to null to avoid printing to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = AddOverlapAdaptation()
    export_rep.run(args=[file, path_str, prefix_str, strategy_str, integration_str])
    
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
    
    print(f"Adapting {base_file} for complete overlap")
    # Create the output for the given representation  
    add_overlap_adaptation(base_file, output_folder, prefix="@brightness_", strategy='brightness', integration='default')
    add_overlap_adaptation(base_file, output_folder, prefix="@text_", strategy='text', integration='default')