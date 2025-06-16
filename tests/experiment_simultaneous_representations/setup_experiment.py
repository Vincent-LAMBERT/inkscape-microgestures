import os
import shutil
import sys

import microrep.core.utils as u
from microrep.add_enhancement import AddEnhancement
from microrep.add_legend import AddLegend
from microrep.complete_occlusion_adaptation import CompleteOcclusionAdaptation
from microrep.core.utils import FINGERS_WITH_THUMB
from microrep.create_representations import CreateRepresentations
from microrep.map_commands import MapCommands

script_path = os.path.dirname(os.path.realpath(__file__))
config_folder = os.path.join(script_path, 'configurations')
output_folder = os.path.join(script_path, 'output')
svg_folder = os.path.join(script_path, 'svg_files')

superimposition_svg = os.path.join(svg_folder, 'Superimposition.svg')
juxtaposition_svg = os.path.join(svg_folder, 'Juxtaposition.svg')
specialSuperimposition_svg = os.path.join(svg_folder, 'SpecialSuperimposition.svg')

representations_folder = os.path.join(output_folder, 'representations')
rep_ts_default = os.path.join(representations_folder, 'TS', 'default')
rep_ts_diversified = os.path.join(representations_folder, 'TS', 'diversified')
rep_th_default = os.path.join(representations_folder, 'TH', 'default')
rep_th_diversified = os.path.join(representations_folder, 'TH', 'diversified')

mappings_folder = os.path.join(output_folder, 'mappings')
command_icons_folder_fr = os.path.join(script_path, 'icons', 'french-commands')
command_icons_folder_en = os.path.join(script_path, 'icons', 'english-commands')
icons_folder = command_icons_folder_en

COMMAND_RADIUS = 2.5
TS = 'TS'  # Partial occlusion condition
TH = 'TH'  # Complete occlusion condition
AANDB = 'AandB'  # A&B family
MAS = 'MaS'  # MaS family

DEFAULT = 'default'
DIVERSIFIED = 'diversified'

################################################################################
# Functions to create hand poses and representations
################################################################################

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
        
def create_representations(file, output_folder, config_file, family, prefix='', one_trajectory_only=False):
    """
    Create the representations for the given hand pose file.
    
    :param file: The hand pose file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    family_str = f"--family={family}"
    one_trajectory_only_str = f"--one_trajectory_only={one_trajectory_only}"
    if prefix:
        prefix_str = f"--prefix={prefix}"
    else:
        prefix_str = ""
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = CreateRepresentations()
    export_rep.run(args=[file, path_str, family_str, config_str, prefix_str, one_trajectory_only_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__

def add_enhancement(file, output_folder, config_file):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = AddEnhancement()
    export_rep.run(args=[file, path_str, config_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__

def add_legend(file, output_folder, config_file):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = AddLegend()
    export_rep.run(args=[file, path_str, config_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__

def complete_occlusion_adaptation(file, output_folder, strategy, integration):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    strategy_str = f"--strategy={strategy}"
    integration_str = f"--integration={integration}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = CompleteOcclusionAdaptation()
    export_rep.run(args=[file, path_str, strategy_str, integration_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__

def map_commands(file, output_folder, config_file, icons_folder, prefix, showMg):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    icons_str = f"--icons={icons_folder}"
    prefix_str = f"--prefix={prefix}"
    showMg_str = f"--showMg={showMg}"
    radius_str = f"--radius={COMMAND_RADIUS}"
    
    # Redirect stdout to null to avoid printing exported files to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = MapCommands()
    export_rep.run(args=[file, path_str, config_str, icons_str, prefix_str, showMg_str, radius_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__
    
################################################################################
# Main function to create the mappings used in the experiment
################################################################################

def compute_base_rep(svg_file, condition, num_fingers):
    """
    Create the representations for the TS or TH condition with 1 or 2 fingers
    :param svg_file: The SVG file to create representations from.
    :param condition: The condition to create representations for (TS or TH).
    :param num_fingers: The number of fingers to create representations for (1 or 2).
    """
    filename = os.path.basename(svg_file).replace('.svg', '')
    condition_rep_folder = os.path.join(representations_folder, condition)
    default_folder = os.path.join(condition_rep_folder, DEFAULT)
    diversified_folder = os.path.join(condition_rep_folder, DIVERSIFIED)
    os.makedirs(default_folder, exist_ok=True)
    os.makedirs(diversified_folder, exist_ok=True)
    
    # Creating representations with config base_{condition}_{num_fingers}.csv
    config_file = os.path.join(config_folder, f'base_{condition}_{num_fingers}.csv')
    create_representations(svg_file, default_folder, config_file, AANDB, prefix=f'{filename}#', one_trajectory_only=False)
    print(f"Created base representations for {filename} in {default_folder} for family {AANDB}")
    create_representations(svg_file, default_folder, config_file, MAS, prefix=f'{filename}#', one_trajectory_only=False)
    print(f"Created base representations for {filename} in {default_folder} for family {MAS}")  
    
    # Diversifying with config style_{case}.csv
    config_file = os.path.join(config_folder, f'style_{condition}.csv')
    for file_name in os.listdir(default_folder):
        if file_name.endswith('.svg'):
            file = os.path.join(default_folder, file_name)
            add_enhancement(file, diversified_folder, config_file)
            print(f"Created enhanced representations for {file_name} in {diversified_folder}")

def duplicate_default_to_text(file_name, condition):
    """
    Duplicate the default representations to create the text representations.
    """
    if condition == TS:
        default_folder = rep_ts_default
        diversified_folder = rep_ts_diversified
    else:
        default_folder = rep_th_default
        diversified_folder = rep_th_diversified
    
    # Copying the file from the default folder to the diversified folder
    default_file = os.path.join(default_folder, file_name)
    # Add a '@text_' instead of the '_' character in the file name 
    file_name = file_name.replace('_', '@text_')
    diversified_file = os.path.join(diversified_folder, file_name)
    if os.path.exists(default_file):
        shutil.copy(default_file, diversified_file)
        print(f"Copied {default_file} to {diversified_file}")
    else:
        raise FileNotFoundError(f"File {default_file} does not exist.")

def adapt_TH_default_superimposition():
    """
    Ensure that SpecialSuperimposition representations are renamed to be 
    the default Superimposition for default and not text diversification
    """
    for file_name in os.listdir(rep_th_default):
        if file_name.startswith('SpecialSuperimposition') and file_name.endswith('.svg'):
            # Rename the SpecialSuperimposition* files to Superimposition* files 
            # (replace the existing files)
            new_file_name = file_name.replace('SpecialSuperimposition', 'Superimposition')
            new_file_path = os.path.join(rep_th_default, new_file_name)
            old_file_path = os.path.join(rep_th_default, file_name)
            if os.path.exists(old_file_path):
                shutil.move(old_file_path, new_file_path)
                print(f"Renamed {old_file_path} to {new_file_path}")
            else:
                raise FileNotFoundError(f"File {old_file_path} does not exist.")
    
    # Delete the remaining SpecialSuperimposition representations
    for file_name in os.listdir(rep_th_diversified):
        if file_name.startswith('SpecialSuperimposition') and file_name.endswith('.svg'):
            file_path = os.path.join(rep_th_diversified, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")
            else:
                raise FileNotFoundError(f"File {file_path} does not exist.")
    
def compute_legends(condition_rep_folder, condition, num_fingers):
    """
    Compute the legends for the representations in the given condition folder.
    """
    config_file = os.path.join(config_folder, f"legend_{condition}_{num_fingers}.csv")
    
    for file_name in os.listdir(condition_rep_folder):
        if file_name.endswith('.svg'):
            file_path = os.path.join(condition_rep_folder, file_name)
            # Create the legend for the given representation
            add_legend(file_path, condition_rep_folder, config_file)
            print(f"Added legend to {file_path}")
            
def compute_superimposition_adaptation(condition_rep_folder):
    """
    Adapt the Superimposition representations in the given condition folder.
    Necessary to make sure every command is visible after applying the map_commands function.
    """
    for file_name in os.listdir(condition_rep_folder):
        if (file_name.startswith('Superimposition') or file_name.startswith('Legended+Superimposition')) and file_name.endswith('.svg'):
            file_path = os.path.join(condition_rep_folder, file_name)
            # Create the adaptation for the given representation
            strategy, integration = get_strat_integration(file_name)
            complete_occlusion_adaptation(file_path, condition_rep_folder, strategy, integration)
            print(f"Adapted {file_path} with strategy {strategy} and integration {integration}")

def get_strat_integration(file_name):
    """
    Extract the strategy and integration from the file name.
    Strategy can be default, brightness or text.
    Integration can be default, or integration.
    """
    if '@brightness' in file_name:
        strategy = 'brightness'
    elif '@text' in file_name:
        strategy = 'text'
    else:
        strategy = 'default'
    
    if 'Legended+' in file_name:
        integration = 'integration'
    else:
        integration = 'default'
    
    return strategy, integration
            
def compute_mappings(condition_rep_folder, condition, num_fingers):
    """
    Compute the mappings for the representations in the given condition folder.
    """
    config_file = os.path.join(config_folder, f"mapping_{condition}_{num_fingers}.csv")
    
    for file_name in os.listdir(condition_rep_folder):
        if file_name.endswith('.svg'):
            file_path = os.path.join(condition_rep_folder, file_name)
            prefix = f"{condition}_{num_fingers}_"
            
            showMg = False
            if '@text' in file_name:
                showMg = True
            
                # Create the mapping for the given representation
                map_commands(file_path, mappings_folder, config_file, icons_folder, prefix, showMg)
                print(f"Mapped commands for {file_path} with prefix '{prefix}'")

def compute_representations(num_fingers):
    """
    Create the representations for the TS and TH condition with 1 or 2 fingers
    :param num_fingers: The number of fingers to create representations for (1 or 2).
    """
    print(f"\n\n#############################################################")
    print(f"####### Computing Superimposition and Juxtaposition  ########")
    print(f"#######     for the partial occlusion condition      ########")
    print(f"#############################################################")
    compute_base_rep(superimposition_svg, TS, num_fingers)
    compute_base_rep(juxtaposition_svg, TS, num_fingers)
    
    print(f"\n\n#############################################################")
    print(f"####### Computing Superimposition and Juxtaposition  ########")
    print(f"#######     for the complete occlusion condition     ########")
    print(f"#############################################################")
    compute_base_rep(superimposition_svg, TH, num_fingers)
    compute_base_rep(juxtaposition_svg, TH, num_fingers)
    compute_base_rep(specialSuperimposition_svg, TH, num_fingers)
    
    print(f"\n\n#############################################################")
    print(f"####### Duplicating the default representation to be  #######") 
    print(f"#######      the base for a text diversification      #######")
    print(f"#############################################################")
    for file_name in os.listdir(rep_ts_default):
        duplicate_default_to_text(file_name, TS)
    for file_name in os.listdir(rep_th_default):
        duplicate_default_to_text(file_name, TH)
    
    print(f"\n\n#############################################################")
    print(f"#######       Adapt the default superimposition       #######")
    print(f"#######         representations to be special         #######")
    print(f"#############################################################")
    adapt_TH_default_superimposition()
    
    print(f"\n\n#############################################################")
    print(f"#######   Adding the legend to the representations    #######")
    print(f"#############################################################")
    compute_legends(rep_ts_default, TS, num_fingers)
    compute_legends(rep_th_default, TH, num_fingers)
    compute_legends(rep_ts_diversified, TS, num_fingers)
    compute_legends(rep_th_diversified, TH, num_fingers)
    
    print(f"\n\n#############################################################")
    print(f"#######            Compute the adaptations            #######")
    print(f"#############################################################")
    compute_superimposition_adaptation(rep_th_default)
    compute_superimposition_adaptation(rep_th_diversified)
    
    print(f"\n\n#############################################################")
    print(f"#######               Map the commands                #######")
    print(f"#############################################################")
    compute_mappings(rep_ts_default, TS, num_fingers)
    compute_mappings(rep_th_default, TH, num_fingers)
    compute_mappings(rep_ts_diversified, TS, num_fingers)
    compute_mappings(rep_th_diversified, TH, num_fingers)

if __name__ == "__main__":
    # Create the output folder
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    # Create the mappings folder
    if not os.path.exists(mappings_folder):
        os.mkdir(mappings_folder)
    else :
        # If the folder already exists, delete its content
        deleteFolderContent(mappings_folder)
    
    # Create the folders if they do not exist
    if not os.path.exists(representations_folder):
        os.mkdir(representations_folder)
    else :
        # If the folder already exists, delete its content
        deleteFolderContent(representations_folder)
    
    print(f"#############################################################")
    print(f"########## Compute representations for one finger ###########")
    print(f"#############################################################")
    compute_representations(1)
    
    # Delete the computes representations to compute the next ones
    shutil.rmtree(representations_folder)
    
    print(f"#############################################################")
    print(f"########## Compute representations for two fingers ###########")
    print(f"#############################################################")
    compute_representations(2)
    
    # Delete the remaining representations
    shutil.rmtree(representations_folder)