#! /usr/bin/env python3

import os
import shutil
import sys

from microrep.export_hand_poses import ExportHandPoses

script_path = os.path.dirname(os.path.realpath(__file__))
base_file = os.path.join(script_path, 'initial.svg')
config_file = os.path.join(script_path, 'config.csv')
export_folder = os.path.join(script_path, 'HandPoses')
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
    print(f"Creating hand poses for {file}")
    
    # self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
    # self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
    #                                 help='Exported file type. One of [svg|png|jpg|pdf]')
    # self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to define the hand poses")
    # self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image")
    # self.arg_parser.add_argument("--markers", type=inkex.Boolean, dest="markers", default=False, help="Show or hide markers on the exported image")
    # self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Print debug messages as warnings")
    # self.arg_parser.add_argument("--dry", type=inkex.Boolean, dest="dry", default=False, help="Don't actually do all of the exports")
    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    
    # Redirect stdout to null to avoid printing to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = ExportHandPoses()
    export_rep.run(args=[file, path_str, config_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__
        
if __name__== "__main__":
    # Create the hand poses folder if it does not exist
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
        
    # Delete the content of the hand poses folder
    deleteFolderContent(export_folder)
    
    # Create the hand poses for the given hand pose  
    create_hand_poses(base_file, export_folder, config_file)