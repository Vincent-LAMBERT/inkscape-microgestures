#! /usr/bin/env python3

import os
import shutil
import sys

from microrep.create_representations import CreateRepresentations

script_path = os.path.dirname(os.path.realpath(__file__))
base_file = os.path.join(script_path, 'initial.svg')
config_file = os.path.join(script_path, 'config.csv')
export_folder = os.path.join(script_path, 'Representations')

def deleteFolderContent(folder):
    for element in os.listdir(folder):
        # If it's a folder, delete it 
        if os.path.isdir(os.path.join(folder, element)):
            shutil.rmtree(os.path.join(folder, element))
        elif os.path.isfile(os.path.join(folder, element)):
            os.remove(os.path.join(folder, element))

def create_representations(file, output_folder, config_file, family):
    """
    Create the representations for the given hand pose file.
    
    :param file: The hand pose file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """
    print(f"Creating representations for {file}")
    
    # self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
    # self.arg_parser.add_argument("--prefix", type=str, dest="prefix", default="", help='Prefix to add to the exported file name (Optional)')
    # self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
    #                                 help='Exported file type. One of [svg|png|jpg|pdf]')
    # self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
    # self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export (Optional)")
    # self.arg_parser.add_argument("--family", type=str, dest="family", default="AandB", help="Selected family")
    # self.arg_parser.add_argument("--traces", type=inkex.Boolean, dest="traces", default=False, help='Show traces')
    # self.arg_parser.add_argument("--command", type=inkex.Boolean, dest="command", default=False, help='Show command placeholders')
    # self.arg_parser.add_argument("--radius", type=float, dest="radius", default=2.5, help="Command radius (temporary)")
    # self.arg_parser.add_argument("--four", type=inkex.Boolean, dest="four", default=False, help='Stop after processing the four first representations of a family')
    # self.arg_parser.add_argument("--one", type=inkex.Boolean, dest="one", default=False, help='Stop after processing one family')
    # self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
    # self.arg_parser.add_argument("--dry", type=inkex.Boolean, dest="dry", default=False, help="Don't actually do all of the exports")
    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    family_str = f"--family={family}"
    
    # Redirect stdout to null to avoid printing to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = CreateRepresentations()
    export_rep.run(args=[file, path_str, family_str, config_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__
        
if __name__== "__main__":
    # Create the representations folder if it does not exist
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
        
    # Delete the content of the representations folder
    deleteFolderContent(export_folder)
    
    # Create the representations for the given hand pose  
    create_representations(base_file, export_folder, config_file, family="AandB")
    create_representations(base_file, export_folder, config_file, family="MaS")