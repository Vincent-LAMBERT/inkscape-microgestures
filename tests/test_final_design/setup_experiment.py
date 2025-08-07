import os
import shutil
import sys

from cairosvgmg import svg2png

import microrep.core.utils as u
from microrep.core.utils import FINGERS_WITH_THUMB
from microrep.create_representations import CreateRepresentations
from microrep.export_hand_poses import ExportHandPoses
from microrep.map_commands import MapCommands

script_path = os.path.dirname(os.path.realpath(__file__))
config_folder = os.path.join(script_path, 'configurations')
output_folder = os.path.join(script_path, 'output')
temp_config_file = os.path.join(script_path, 'temp_config_file.csv')
base_file_left = os.path.join(script_path, 'base_left.svg')
base_file_right = os.path.join(script_path, 'base_right.svg')
hand_poses_folder = os.path.join(output_folder, 'hand-poses')
representations_folder = os.path.join(output_folder, 'representations')

mappings_training_folder = os.path.join(output_folder, 'mappings-training')
mappings_experiment_folder = os.path.join(output_folder, 'mappings-experiment')
command_icons_folder_fr = os.path.join(script_path, 'icons', 'french-commands')
command_icons_folder_en = os.path.join(script_path, 'icons', 'english-commands')

smartwatch_experiment_folder = os.path.join(output_folder, 'smartwatch-export')

COMMAND_RADIUS = 7

################################################################################
# Commands and mappings
################################################################################

# French version
FR_BASEBALL = "Baseball"
FR_BASKETBALL = "Basketball"
FR_BOOT = "Botte"
FR_BOWLING = "Bowling"
FR_BOWTIE = "Noeud papillon"
FR_BUTTON = "Bouton"
FR_CARDS = "Cartes"
FR_CHESS = "Echecs"
FR_CLOCK = "Horloge"
FR_COAT = "Veste"
FR_DARTS = "Flechettes"
FR_DICE = "Des"
FR_ENVELOPE = "Enveloppe"
FR_GLOVES = "Gants"
FR_HAT = "Chapeau"
FR_HOCKEY = "Hockey"
FR_KARATE = "Karate"
FR_KEYBOARD = "Clavier"
FR_PAPERCLIP = "Trombonne"
FR_POOL = "Piscine"
FR_PRINTER = "Imprimante"
FR_SKIRT = "Jupe"
FR_STAPLER = "Agraffeuse"
FR_SWEATER = "Sweat"
FR_TENNIS = "Tennis"
FR_TROUSERS = "Jean"
FR_TSHIRT = "Tshirt"


FR_ACORN = "Gland"
FR_APPLE = "Pomme"
FR_ARTICHOKE = "Artichaud"
FR_AVOCADO = "Avocat"
FR_BANANA = "Banane"
FR_BLUEBERRY = "Myrtille"
FR_BROCCOLI = "Brocoli"
FR_CABBAGE = "Chou"
FR_CARROT = "Carotte"
FR_CHERRY = "Cerise"
FR_CORN = "Mais"
FR_CUCUMBER = "Concombre"
FR_EGGPLANT = "Aubergine"
FR_FIG = "Figue"
FR_GARLIC = "Ail"
FR_GRAPES = "Raisin"
FR_KIWI = "Kiwi"
FR_LEMON = "Citron"
FR_LETTUCE = "Salade"
FR_MUSHROOM = "Champignon"
FR_ONION = "Oignon"
FR_PEACH = "Peche"
FR_PEAR = "Poire"
FR_PEPPER = "Poivre"
FR_PINEAPPLE = "Ananas"
FR_PLUM = "Prune"
FR_POTATO = "Patate"
FR_PUMPKIN = "Citrouille"
FR_STRAWBERRY = "Fraise"
FR_WATERMELON = "Pasteque"


# English version
EN_BASEBALL = "Baseball"  # Should not be used with basketball
EN_BASKETBALL = "Basketball"  # Should not be used with baseball
EN_BOOT = "Boot"
EN_BOWLING = "Bowling"
EN_BOWTIE = "Bowtie"
EN_BUTTON = "Button"
EN_CARDS = "Cards"
EN_CHESS = "Chess"
EN_CLOCK = "Clock"
EN_COAT = "Coat"
EN_DARTS = "Darts"
EN_DICE = "Dice"
EN_ENVELOPE = "Envelope"
EN_GLOVES = "Gloves"
EN_HAT = "Hat"
EN_HOCKEY = "Hockey"
EN_KARATE = "Karate"
EN_KEYBOARD = "Keyboard"
EN_PAPERCLIP = "Paperclip"
EN_POOL = "Pool"
EN_PRINTER = "Printer"
EN_SKIRT = "Skirt"
EN_STAPLER = "Stapler"
EN_SWEATER = "Sweater"
EN_TENNIS = "Tennis"
EN_TROUSERS = "Trousers"
EN_TSHIRT = "Tshirt"


EN_ACORN = "Acorn"
EN_APPLE = "Apple"
EN_ARTICHOKE = "Artichoke"
EN_AVOCADO = "Avocado"
EN_BANANA = "Banana"
EN_BLUEBERRY = "Blueberry"
EN_BROCCOLI = "Broccoli" # Should not be used with lettuce
EN_CABBAGE = "Cabbage"
EN_CARROT = "Carrot"
EN_CHERRY = "Cherry"
EN_CORN = "Corn"
EN_CUCUMBER = "Cucumber"
EN_EGGPLANT = "Eggplant"
EN_FIG = "Fig"
EN_GARLIC = "Garlic"
EN_GRAPES = "Grapes"
EN_KIWI = "Kiwi"
EN_LEMON = "Lemon"
EN_LETTUCE = "Lettuce" # Should not be used with broccoli
EN_MUSHROOM = "Mushroom"
EN_ONION = "Onion"
EN_PEACH = "Peach"
EN_PEAR = "Pear"
EN_PEPPER = "Pepper"
EN_PINEAPPLE = "Pineapple"
EN_PLUM = "Plum"
EN_POTATO = "Potato"
EN_PUMPKIN = "Pumpkin"
EN_STRAWBERRY = "Strawberry"
EN_WATERMELON = "Watermelon"


command_mapping_training_fr = {u.TAP : {u.TIP: {u.INDEX: FR_BASEBALL, u.MIDDLE: FR_BASKETBALL, u.RING: FR_BOWLING, u.PINKY: FR_HOCKEY},
                            u.NAIL: {u.INDEX: FR_TROUSERS, u.MIDDLE: FR_SKIRT, u.RING: FR_SWEATER, u.PINKY: FR_COAT},
                            u.SIDE: {u.INDEX: FR_HAT, u.MIDDLE: FR_BOWTIE, u.RING: FR_GLOVES, u.PINKY: FR_CHESS}},
                   u.SWIPE : {u.UP: {u.INDEX_MIDDLE: FR_DARTS,
                                       u.MIDDLE_RING: FR_TENNIS,
                                       u.RING_PINKY: FR_POOL},
                              u.DOWN: {u.INDEX_MIDDLE: FR_STAPLER,
                                       u.MIDDLE_RING: FR_PRINTER,
                                       u.RING_PINKY: FR_ENVELOPE},
                              u.LEFT: {u.INDEX_MIDDLE_RING: FR_TSHIRT, 
                                        u.MIDDLE_RING_PINKY: FR_BOOT, 
                                        u.INDEX_MIDDLE_RING_PINKY: FR_CARDS},
                              u.RIGHT: {u.INDEX_MIDDLE_RING: FR_CLOCK, 
                                        u.MIDDLE_RING_PINKY: FR_KEYBOARD, 
                                        u.INDEX_MIDDLE_RING_PINKY: FR_PAPERCLIP}}}

command_mapping_training_en = {u.TAP : {u.TIP: {u.INDEX: EN_BASEBALL, u.MIDDLE: EN_BASKETBALL, u.RING: EN_BOWLING, u.PINKY: EN_HOCKEY},
                            u.NAIL: {u.INDEX: EN_TROUSERS, u.MIDDLE: EN_SKIRT, u.RING: EN_SWEATER, u.PINKY: EN_COAT},
                            u.SIDE: {u.INDEX: EN_HAT, u.MIDDLE: EN_BOWTIE, u.RING: EN_GLOVES, u.PINKY: EN_CHESS}},
                   u.SWIPE : {u.UP: {u.INDEX_MIDDLE: EN_DARTS,
                                       u.MIDDLE_RING: EN_TENNIS,
                                       u.RING_PINKY: EN_POOL},
                              u.DOWN: {u.INDEX_MIDDLE: EN_STAPLER,
                                       u.MIDDLE_RING: EN_PRINTER,
                                       u.RING_PINKY: EN_ENVELOPE},
                              u.LEFT: {u.INDEX_MIDDLE_RING: EN_TSHIRT, 
                                        u.MIDDLE_RING_PINKY: EN_BOOT, 
                                        u.INDEX_MIDDLE_RING_PINKY: EN_CARDS},
                              u.RIGHT: {u.INDEX_MIDDLE_RING: EN_CLOCK, 
                                        u.MIDDLE_RING_PINKY: EN_KEYBOARD, 
                                        u.INDEX_MIDDLE_RING_PINKY: EN_PAPERCLIP}}}

command_mapping_experiment_fr = {u.TAP : {u.TIP: {u.INDEX: FR_EGGPLANT, u.MIDDLE: FR_ARTICHOKE, u.RING: FR_PEAR, u.PINKY: FR_POTATO},
                            u.NAIL: {u.INDEX: FR_PUMPKIN, u.MIDDLE: FR_STRAWBERRY, u.RING: FR_ONION, u.PINKY: FR_PLUM},
                            u.SIDE: {u.INDEX: FR_AVOCADO, u.MIDDLE: FR_KIWI, u.RING: FR_GRAPES, u.PINKY: FR_LEMON}},
                   u.SWIPE : {u.UP: {u.INDEX_MIDDLE: FR_APPLE,
                                       u.MIDDLE_RING: FR_ACORN,
                                       u.RING_PINKY: FR_BLUEBERRY},
                              u.DOWN: {u.INDEX_MIDDLE: FR_MUSHROOM,
                                       u.MIDDLE_RING: FR_WATERMELON,
                                       u.RING_PINKY: FR_CHERRY},
                              u.LEFT: {u.INDEX_MIDDLE_RING: FR_FIG, 
                                        u.MIDDLE_RING_PINKY: FR_CABBAGE, 
                                        u.INDEX_MIDDLE_RING_PINKY: FR_BROCCOLI},
                              u.RIGHT: {u.INDEX_MIDDLE_RING: FR_CUCUMBER, 
                                        u.MIDDLE_RING_PINKY: FR_CARROT, 
                                        u.INDEX_MIDDLE_RING_PINKY: FR_PINEAPPLE}}}

command_mapping_experiment_en = {u.TAP : {u.TIP: {u.INDEX: EN_EGGPLANT, u.MIDDLE: EN_ARTICHOKE, u.RING: EN_PEAR, u.PINKY: EN_POTATO},
                            u.NAIL: {u.INDEX: EN_PUMPKIN, u.MIDDLE: EN_STRAWBERRY, u.RING: EN_ONION, u.PINKY: EN_PLUM},
                            u.SIDE: {u.INDEX: EN_AVOCADO, u.MIDDLE: EN_KIWI, u.RING: EN_GRAPES, u.PINKY: EN_LEMON}},
                   u.SWIPE : {u.UP: {u.INDEX_MIDDLE: EN_APPLE,
                                       u.MIDDLE_RING: EN_ACORN,
                                       u.RING_PINKY: EN_BLUEBERRY},
                              u.DOWN: {u.INDEX_MIDDLE: EN_MUSHROOM,
                                       u.MIDDLE_RING: EN_WATERMELON,
                                       u.RING_PINKY: EN_CHERRY},
                              u.LEFT: {u.INDEX_MIDDLE_RING: EN_FIG, 
                                        u.MIDDLE_RING_PINKY: EN_CABBAGE, 
                                        u.INDEX_MIDDLE_RING_PINKY: EN_BROCCOLI},
                              u.RIGHT: {u.INDEX_MIDDLE_RING: EN_CUCUMBER, 
                                        u.MIDDLE_RING_PINKY: EN_CARROT, 
                                        u.INDEX_MIDDLE_RING_PINKY: EN_PINEAPPLE}}}

commands_for_posture = {u.FRONT: {u.UP: {u.TAP: [u.TIP]},
                                 u.CLOSE: {u.TAP: [u.NAIL]},
                                 u.ABDUCTION: {u.SWIPE: [u.UP, u.DOWN]},
                                 u.ADDUCTION: {u.SWIPE: [u.UP, u.DOWN]},
                                 u.COMPLEX: {u.SWIPE: [u.LEFT, u.RIGHT]}},
                       u.FRONT_RIGHT: {u.UP: {u.TAP: [u.TIP, u.SIDE]},
                                       u.FLEX: {u.TAP: [u.SIDE]},
                                       u.CLOSE: {u.TAP: [u.NAIL, u.SIDE]},
                                       u.ABDUCTION: {u.SWIPE: [u.UP, u.DOWN]},
                                       u.ADDUCTION: {u.SWIPE: [u.UP, u.DOWN]},
                                       u.COMPLEX: {u.SWIPE: [u.LEFT, u.RIGHT]}}, 
                       u.RIGHT: {u.UP: {u.TAP: [u.SIDE]},
                                 u.FLEX: {u.TAP: [u.SIDE]},
                                 u.CLOSE: {u.TAP: [u.SIDE]}}}

################################################################################
# Functions to create the right config file for the representations and mappings
# issued from the different hand poses
################################################################################

def create_simultaneous_config_dict_for_pose(file):
    """
    Create the representations corresponding to the experiment command mapping and the hand pose
    """
    wrist_orient = u.get_wrist_orientation_name(file.split("_")[0])
    if not wrist_orient in commands_for_posture.keys():
        return None
    
    commands_for_orient = commands_for_posture[wrist_orient]
    fingers_with_status = {}
    for finger_with_status in file.split("_")[1].split(".")[0].split("-"):
        finger = u.get_finger_name(finger_with_status[:-1])
        status = u.get_status_name(finger_with_status[-1])
        fingers_with_status[finger] = status
    
    # Create a dictionnary with the shape {'index': {'tap': ['tip', 'side']}, 'middle': {'tap': ['tip', 'side']}, 'ring': {'tap': ['tip', 'side']}, 'pinky': {'tap': ['tip', 'side']}} to store the config_dict fingers and their corresponding microgestures for the detected posture
    
    joined_fingers = []
    config_dict = {finger:None for finger in u.FINGERS.copy()}
    
    for finger, status in fingers_with_status.items():
        if finger != u.THUMB and (status == u.UP or status == u.FLEX or status == u.CLOSE):
            if status in commands_for_orient.keys():
                config_dict[finger] = commands_for_orient[status]
            else :
                config_dict[finger] = {}
        elif status == u.ADDUCTION:
            if finger == u.INDEX:
                # The adducted finger is the index and the abducted is the middle 
                config_dict.pop(u.INDEX)
                config_dict.pop(u.MIDDLE)
                config_dict[u.INDEX + '-' + u.MIDDLE] = commands_for_orient[u.ADDUCTION]
            elif finger == u.MIDDLE:
                # The adducted finger is the middle and the abducted is the ring
                config_dict.pop(u.MIDDLE)
                config_dict.pop(u.RING)
                config_dict[u.MIDDLE + '-' + u.RING] = commands_for_orient[u.ADDUCTION]
            elif finger == u.RING:
                # The adducted finger is the ring and the abducted is the pinky
                config_dict.pop(u.RING)
                config_dict.pop(u.PINKY)
                config_dict[u.RING + '-' + u.PINKY] = commands_for_orient[u.ADDUCTION]
        elif status == u.COMPLEX:
            config_dict.pop(finger)
            joined_fingers.append(finger)
            
    if len(joined_fingers) > 0:
        config_dict['-'.join(joined_fingers)] = commands_for_orient[u.COMPLEX]
    
    config_dict = remove_side_in_adjacent_fingers_with_same_state(config_dict, fingers_with_status, wrist_orient)
    
    return config_dict

def remove_side_in_adjacent_fingers_with_same_state(config_dict, fingers_with_status, wrist_orient):
    """
    Evaluate the states of all the fingers and make sure the side microgestures 
    are only depicted when the finger is not obstructed by another finger
    """
    fingers_with_priority = {u.INDEX: fingers_with_status[u.INDEX]}
    for finger, status in fingers_with_status.items():
        status_prioritized = [s for s in fingers_with_priority.values()]
        if wrist_orient == u.RIGHT:
            if (status == u.UP and not u.UP in status_prioritized) or (status in [u.FLEX, u.CLOSE] and not (u.CLOSE in status_prioritized)):
                fingers_with_priority[finger] = status
        else :
            if (status == u.UP and not u.UP in status_prioritized) or (status in [u.FLEX, u.CLOSE] and not (u.CLOSE in status_prioritized or u.FLEX in status_prioritized)):
                fingers_with_priority[finger] = status
    
    new_config_dict = {}
    for finger in config_dict.keys():
        if finger in fingers_with_priority:
            new_config_dict[finger] = config_dict[finger]
        else :
            for mg_type, mg_characs in config_dict[finger].items():
                if u.SIDE in mg_characs:
                    new_characs = mg_characs.copy()
                    new_characs.remove(u.SIDE)
                    new_config_dict[finger] = {mg_type: new_characs}
                else:
                    new_config_dict[finger] = {mg_type: mg_characs}
    
    # Send none if for every finger the config is empty
    if all([config == {} for config in new_config_dict.values()]):
        return None
    return new_config_dict
    
def create_rep_config_file(config_dict):
    """
    Create a string with the shape index+tap-tip,index+tap-side,middle+tap-tip,middle+tap-side,ring+tap-tip,ring+tap-side,pinky+tap-tip,pinky+tap-side from the previously created dictionnary
    """
    config_string = ""
    for finger, microgesture in config_dict.items():
        for mg_type, mg_characs in microgesture.items():
            for mg_charac in mg_characs:
                config_string += f"{finger}+{mg_type}-{mg_charac},"
    config_string = config_string[:-1]
    
    with open(temp_config_file, 'w') as f:
        f.write(config_string)
    return temp_config_file

def create_mapping_config_file(config_dict, command_mapping):
    """
    Create a string with the shape index+tap_tip-command,index+tap_side-command,middle+tap_tip-command,middle+tap_side-command,ring+tap_tip-command,ring+tap_side-command,pinky+tap_tip-command,pinky+tap_side-command from the previously created dictionnary
    """
    config_string = ""
    for finger, microgesture in config_dict.items():
        for mg_type, mg_characs in microgesture.items():
            for mg_charac in mg_characs:
                # print(f"mg_type: {mg_type}, command_mapping[mg_type]: {command_mapping[mg_type]}")
                config_string += f"{finger}+{mg_type}_{mg_charac}-{command_mapping[mg_type][mg_charac][finger]},"
    config_string = config_string[:-1]
    
    with open(temp_config_file, 'w') as f:
        f.write(config_string)
    return temp_config_file
        
def get_label_from_hand_pose(orient, hand_pose):
    """
    Has as input a hand pose of the form [(finger, status), (finger, status), ...]
    Returns a string of the form 'Finger1status1-Finger2status2-...'
    """
    label = u.get_wrist_orientation_nickname(orient)+"_"
    for finger, status in hand_pose:
        finger_nick = u.get_finger_nickname(finger)
        status_nick = u.get_status_nickname(status).lower()
        label += finger_nick+status_nick+"-"
    label = label[:-1]
    return label

def get_one_by_one_configs_for_pose(wanted_pose, config_file):
    """
    Return the list of configs corresponding to the wanted pose 
    among the configurations (one by one condition)
    """
    config_dict = {}
    with open(config_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace("\n", "")
            pose, config = line.split(",")
            
            # handle pose
            orient, finger_poses = pose.split("_")
            finger_poses = finger_poses.split("-")
            hand_pose = [(FINGERS_WITH_THUMB[i], finger_poses[i]) for i in range(len(FINGERS_WITH_THUMB))]
            pose = get_label_from_hand_pose(orient, hand_pose)
            
            # handle config
            finger, mg_charac = config.split("+")
            mg, charac = mg_charac.split("_")
            
            if not pose in config_dict:
                config_dict[pose] = [{finger: {mg: [charac]}}]
            else :
                config_dict[pose].append({finger: {mg: [charac]}})
    return config_dict[wanted_pose]

def get_simultaneous_config_for_pose(wanted_pose, config_file):
    """
    Return the list of configs corresponding to the wanted pose 
    among the configurations (simultaneous condition)
    """
    config_dict = {}
    with open(config_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace("\n", "")
            pose = line.split(",")[0]
            # handle pose
            orient, finger_poses = pose.split("_")
            finger_poses = finger_poses.split("-")
            hand_pose = [(FINGERS_WITH_THUMB[i], finger_poses[i]) for i in range(len(FINGERS_WITH_THUMB))]
            pose = get_label_from_hand_pose(orient, hand_pose)
            
            # handle config
            configs = line.split(",")[1:]
            for config in configs:
                finger, mg_charac = config.split("+")
                mg, charac = mg_charac.split("_")
                
                if not pose in config_dict:
                    config_dict[pose] = {finger: {mg: [charac]}}
                else :  
                    if not finger in config_dict[pose]:
                        config_dict[pose][finger] = {mg: [charac]}
                    else :
                        if not mg in config_dict[pose][finger]:
                            config_dict[pose][finger][mg] = [charac]
                        else :
                            config_dict[pose][finger][mg].append(charac)
    return config_dict[wanted_pose]

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

def create_hand_poses(file, output_folder, config_file):
    """
    Create the hand poses for the given hand pose file.
    
    :param file: The hand pose file to create hand poses for.
    :param output_folder: The folder to save the hand poses in.
    :param config_dict: The configuration dictionary for the hand poses.
    """    
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

def copy_or_create_representations(file, output_folder, config_dict, family):
    hand_pose_file = os.path.join(hand_poses_folder, file)
    if config_dict == None or config_dict == {}:
        shutil.copy(hand_pose_file, output_folder)
    else :
        print(f"Creating representations for {file}")
        rep_config_file = create_rep_config_file(config_dict)
        create_representations(hand_pose_file, output_folder, rep_config_file, family)
        
def create_representations(file, output_folder, config_file, family):
    """
    Create the representations for the given hand pose file.
    
    :param file: The hand pose file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
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

def copy_or_map_commands(file, output_folder, folder_for_file, config_dict, command_mapping, icon_folder, output_name=None):
    if output_name == None:
        output_name = folder_for_file.split(os.sep)[-1]
    
    representation_file = os.path.join(folder_for_file, file)
    if config_dict == None or config_dict == {}:
        shutil.copy(representation_file, output_folder)
    else :
        print(f"Creating mapping for {file}")
        mapping_config_file = create_mapping_config_file(config_dict, command_mapping)
        map_commands(representation_file, output_folder, mapping_config_file, icon_folder, output_name)

def map_commands(file, output_folder, config_file, icons_folder, output_name):
    """
    Create the representations for the given representation file.
    
    :param file: The representation file to create representations for.
    :param output_folder: The folder to save the representations in.
    :param config_dict: The configuration dictionary for the representations.
    """    
    path_str = f"--path={output_folder}"
    config_str = f"--config={config_file}"
    icons_str = f"--icons={icons_folder}"
    output_name_str = f"--name={output_name}"
    radius_str = f"--radius={COMMAND_RADIUS}"
    
    # Redirect stdout to null to avoid printing to console
    sys.stdout = open(os.devnull, 'w')
    
    export_rep = MapCommands()
    export_rep.run(args=[file, path_str, config_str, icons_str, output_name_str, radius_str])
    
    # Close the redirected stdout
    sys.stdout.close()
    # Restore stdout to default
    sys.stdout = sys.__stdout__
    
################################################################################
# Main function to create the mappings used in the experiment
################################################################################

def convert_to_png(folder):
    """
    Convert the svg files in the given folder to png files.
    
    :param folder: The folder containing the svg files to convert.
    """
    print(f"\nConverting svg files to png in {folder}")
    for file in os.listdir(folder):
        if file.endswith(".svg"):
            filename = os.path.join(folder, file)
            with open(filename, 'r') as f:
                svg_code = f.read()
                png_filename = filename.replace(".svg", ".png")
                svg2png(bytestring=svg_code,write_to=png_filename)
            # Delete the original svg file
            os.remove(filename)

def copy_folder_content_to_smartwatch_experiment_folder(folder, smartwatch_experiment_folder, nick=None):
    """
    Copy the files in the given folder to the smartwatch experiment folder.
    
    :param folder: The folder containing the files to copy.
    :param smartwatch_experiment_folder: The folder to copy the files to.
    """
    for file in os.listdir(folder):
        shutil.copy(os.path.join(folder, file), smartwatch_experiment_folder)
        if nick!=None:
            new_file = f"{nick}_{file}"
        else :
            new_file = file
        new_file = new_file.replace("-", "_").lower()
        new_file = os.path.join(smartwatch_experiment_folder, new_file)
        os.rename(os.path.join(smartwatch_experiment_folder, file), new_file)
        
def create_swipe_one_by_one_representations(base_file, family, counter=0):
    """
    Invoke the functions to create the representations 
    for the SwipeOneByOne condition of the experiment
    """
    icon_folder = command_icons_folder_fr
    config_file = os.path.join(config_folder, 'config_one_by_one_hand_poses.csv')
    config_rep_file = os.path.join(config_folder, 'config_one_by_one_hand_poses_rep.csv')
    mappings_folder = os.path.join(output_folder, 'mappings-one-by-one')
    # Create the mappings folder if it does not exist
    if not os.path.exists(mappings_folder):
        os.mkdir(mappings_folder)
    
    # Deleting the previous content of the folders
    deleteFolderContent(mappings_folder)
    deleteFolderContent(hand_poses_folder)
    
    ### STEP 1 - Creating the hand poses files
    create_hand_poses(base_file, hand_poses_folder, config_file)
    
    for file in os.listdir(hand_poses_folder):
        # Creating a subfolder for each representation file
        representations_folder_for_file = os.path.join(representations_folder, file.split(".")[0])
        if os.path.exists(representations_folder_for_file):
            shutil.rmtree(os.path.join(representations_folder_for_file))
        os.mkdir(representations_folder_for_file)
        
        # The configuration dictionnary to create single-picture representations depends on the hand pose
        # Hence, we need to get the config dict for the current file
        config_dicts = get_one_by_one_configs_for_pose(file.split(".")[0], config_rep_file)
        
        for config_dict in config_dicts:
            ## STEP 2 - Creating the representations for the hand pose    
            # If the config_dict is empty, there is no representation to create for this hand pose.
            # As for this experiment, we still need empty representations, we copy the initial file    
            copy_or_create_representations(file, representations_folder_for_file, config_dict, family)
            
            for subfile in os.listdir(representations_folder_for_file):
                ## STEP 3 - Creating the mappings for each created representation  
                # If the config_dict is empty, there is no mapping to create for this representation.
                # As for this experiment, we still need empty representations, we copy the initial file 
                # name = f"{family}_training_right_fr_one_by_one_{counter}"
                # copy_or_map_commands(subfile, mappings_folder, representations_folder_for_file, config_dict, command_mapping_training_fr, icon_folder, output_name=name)
                name = f"{family}_experiment_right_fr_one_by_one_{counter}"
                copy_or_map_commands(subfile, mappings_folder, representations_folder_for_file, config_dict, command_mapping_experiment_fr, icon_folder, output_name=name)
                counter += 1
            
            # Deleting files in the representations folder made for the hand pose
            deleteFolderContent(representations_folder_for_file)
        
    ### STEP 4 - Convert to png 
    # (svg cannot be imported as drawable in the kotlin app)
    # convert_to_png(mappings_folder)
            
    ### STEP 5 - Copy to the smartwatch experiment folder 
    copy_folder_content_to_smartwatch_experiment_folder(mappings_folder, smartwatch_experiment_folder)
    
    # Delete the mappings folder
    shutil.rmtree(mappings_folder)
        
def create_swipe_multiple_representations(base_file, config_file, config_rep_file, family, counter=0):
    """
    Invoke the functions to create the representations 
    for the SwipeMultiple condition of the experiment
    """
    icon_folder = command_icons_folder_fr
    mappings_folder = os.path.join(output_folder, 'mappings-simultaneous')
    # Create the mappings folder if it does not exist
    if not os.path.exists(mappings_folder):
        os.mkdir(mappings_folder)
    
    # Deleting the previous content of the folders
    deleteFolderContent(mappings_folder)
    deleteFolderContent(hand_poses_folder)
    
    ### STEP 1 - Creating the hand poses files
    create_hand_poses(base_file, hand_poses_folder, config_file)
    
    for file in os.listdir(hand_poses_folder):        
        # Creating a subfolder for each representation file
        representations_folder_for_file = os.path.join(representations_folder, file.split(".")[0])
        if os.path.exists(representations_folder_for_file):
            shutil.rmtree(os.path.join(representations_folder_for_file))
        os.mkdir(representations_folder_for_file)
        
        # The configuration dictionnary to create simultaneous representations depends on the hand pose
        # Hence, we need to get the config dict for the current file
        config_dict = get_simultaneous_config_for_pose(file.split(".")[0], config_rep_file)
        
        ## STEP 2 - Creating the representations for the hand pose    
        # If the config_dict is empty, there is no representation to create for this hand pose.
        # As for this experiment, we still need empty representations, we copy the initial file    
        copy_or_create_representations(file, representations_folder_for_file, config_dict, family)
        
        ## STEP 3 - Creating the mappings for each created representation   
        for subfile in os.listdir(representations_folder_for_file):
            # If the config_dict is empty, there is no mapping to create for this representation.
            # As for this experiment, we still need empty representations, we copy the initial file   
            # name = f"{family}_training_right_fr_simultaneous_{counter}"
            # copy_or_map_commands(subfile, mappings_folder, representations_folder_for_file, config_dict, command_mapping_training_fr, icon_folder, output_name=name)
            name = f"{family}_experiment_right_fr_simultaneous_{counter}"
            copy_or_map_commands(subfile, mappings_folder, representations_folder_for_file, config_dict, command_mapping_experiment_fr, icon_folder, output_name=name)
            counter += 1
        
        # Deleting files in the representations folder made for the hand pose
        deleteFolderContent(representations_folder_for_file)
        
    ### STEP 4 - Convert to png 
    # (svg cannot be imported as drawable in the kotlin app)
    # convert_to_png(mappings_folder)
    
    ### STEP 5 - Copy to the smartwatch experiment folder 
    copy_folder_content_to_smartwatch_experiment_folder(mappings_folder, smartwatch_experiment_folder)
    
    # Delete the mappings folder
    shutil.rmtree(mappings_folder)
    
def get_mimic_hand_pose_configurations():
    """
    Return the configurations for the MimicHandPose 
    condition of the experiment.
    """
    configurations = []
    # config = {"name": "Training for left hand (french commands)", "nickname": "training_left_fr", "folder": os.path.join(mappings_training_folder, 'left', 'french'), "file": base_file_left, "command_mapping": command_mapping_training_fr, "icon_folder": command_icons_folder_fr}
    # configurations.append(config)
    # config = {"name": "Experiment for left hand (french commands)", "nickname": "experiment_left_fr", "folder": os.path.join(mappings_experiment_folder, 'left', 'french'), "file": base_file_left, "command_mapping": command_mapping_experiment_fr, "icon_folder": command_icons_folder_fr}
    # configurations.append(config)
    # config = {"name": "Training for left hand (english commands)", "nickname": "training_left_en", "folder": os.path.join(mappings_training_folder, 'left', 'english'), "file": base_file_left, "command_mapping": command_mapping_training_en, "icon_folder": command_icons_folder_en}
    # configurations.append(config)
    # config = {"name": "Experiment for left hand (english commands)", "nickname": "experiment_left_en", "folder": os.path.join(mappings_experiment_folder, 'left', 'english'), "file": base_file_left, "command_mapping": command_mapping_experiment_en, "icon_folder": command_icons_folder_en}
    # configurations.append(config)
    config = {"name": "Training for right hand (french commands)", "nickname": "training_right_fr", "folder": os.path.join(mappings_training_folder, 'right', 'french'), "file": base_file_right, "command_mapping": command_mapping_training_fr, "icon_folder": command_icons_folder_fr}
    configurations.append(config)
    config = {"name": "Experiment for right hand (french commands)", "nickname": "experiment_right_fr", "folder": os.path.join(mappings_experiment_folder, 'right', 'french'), "file": base_file_right, "command_mapping": command_mapping_experiment_fr, "icon_folder": command_icons_folder_fr}
    configurations.append(config)
    # config = {"name": "Training for right hand (english commands)", "nickname": "training_right_en", "folder": os.path.join(mappings_training_folder, 'right', 'english'), "file": base_file_right, "command_mapping": command_mapping_training_en, "icon_folder": command_icons_folder_en}
    # configurations.append(config)
    # config = {"name": "Experiment for right hand (english commands)", "nickname": "experiment_right_en", "folder": os.path.join(mappings_experiment_folder, 'right', 'english'), "file": base_file_right, "command_mapping": command_mapping_experiment_en, "icon_folder": command_icons_folder_en}
    # configurations.append(config)
    return configurations

def create_mimic_hand_pose_representations(family):  
    """
    Invoke the functions to create the representations 
    for the MimicHandPose condition of the experiment
    """
    configurations = get_mimic_hand_pose_configurations()
    config_file = os.path.join(config_folder, 'config_export_hand_poses.csv')
    
    for config in configurations:
        base_file = config["file"]
        command_mapping = config["command_mapping"]
        icon_folder = config["icon_folder"]
        mappings_folder = config["folder"]
        # Create the mappings folder if it does not exist
        if not os.path.exists(mappings_folder):
            os.makedirs(mappings_folder)
        
        # Deleting the previous content of the folders
        deleteFolderContent(hand_poses_folder)
        deleteFolderContent(representations_folder)
        
        ### STEP 1 - Creating the hand poses files 
        # we have to do it here because they can be for the right 
        # or the left hand depending on the configuration
        create_hand_poses(base_file, hand_poses_folder, config_file)
    
        for file in os.listdir(hand_poses_folder):
            # Creating a subfolder for each representation file
            representations_folder_for_file = os.path.join(representations_folder, file.split(".")[0])
            os.mkdir(representations_folder_for_file)
        
            # The configuration dictionnary to create simultaneous representations depends on the hand pose
            # Hence, we need to get the config dict for the current file
            config_dict = create_simultaneous_config_dict_for_pose(file)
            
            ## STEP 2 - Creating the representations for the hand pose    
            # If the config_dict is empty, there is no representation to create for this hand pose.
            # As for this experiment, we still need empty representations, we copy the initial file    
            copy_or_create_representations(file, representations_folder_for_file, config_dict, family)
            
            ## STEP 3 - Creating the mappings for each created representation   
            for subfile in os.listdir(representations_folder_for_file):
                # If the config_dict is empty, there is no mapping to create for this representation.
                # As for this experiment, we still need empty representations, we copy the initial file   
                copy_or_map_commands(subfile, mappings_folder, representations_folder_for_file, config_dict, command_mapping, icon_folder)
        
        ### STEP 4 - Convert to png 
        # (svg cannot be imported as drawable in the kotlin app)
        # convert_to_png(mappings_folder)
    
        # ### STEP 5 - Copy to the smartwatch experiment folder 
        # Add to each copied file the output_name corresponding to the configuration
        nick = config["nickname"]
        copy_folder_content_to_smartwatch_experiment_folder(mappings_folder, smartwatch_experiment_folder, nick)
        
        # Delete the mappings folder
        shutil.rmtree(mappings_folder)  

if __name__ == "__main__":
    # Create the output folder
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    # Create the smartwatch experiment folder
    if not os.path.exists(smartwatch_experiment_folder):
        os.mkdir(smartwatch_experiment_folder)
    else :
        # If the folder already exists, delete its content
        deleteFolderContent(smartwatch_experiment_folder)
    
    # Create the folders if they do not exist
    if not os.path.exists(hand_poses_folder):
        os.mkdir(hand_poses_folder)
    if not os.path.exists(representations_folder):
        os.mkdir(representations_folder)
    if not os.path.exists(mappings_training_folder):
        os.mkdir(mappings_training_folder)
    if not os.path.exists(mappings_experiment_folder):
        os.mkdir(mappings_experiment_folder)
        
        
    # Setting up the variables for the simultaneous hand poses
    base_aandb = os.path.join(script_path, 'base_aandb.svg')
    base_aandb_spec = os.path.join(script_path, 'base_aandb_spec.svg')
    base_mas = os.path.join(script_path, 'base_mas.svg')
    
    print(f"\n\n#############################################################")
    print(f"########   Creating SwipeOneByOne representations   #########")
    print(f"#############################################################")
    create_swipe_one_by_one_representations(base_aandb, 'AandB')
    create_swipe_one_by_one_representations(base_mas, 'MaS')
    
    print(f"\n\n#############################################################")
    print(f"########   Creating SwipeMultiple representations   #########")
    print(f"#############################################################")
    config_file = os.path.join(config_folder, 'config_simultaneous_hand_poses.csv')
    config_rep_file = os.path.join(config_folder, 'config_simultaneous_hand_poses_rep.csv')
    create_swipe_multiple_representations(base_aandb, config_file, config_rep_file, 'AandB')
    create_swipe_multiple_representations(base_mas, config_file, config_rep_file, 'MaS')
    
    config_file = os.path.join(config_folder, 'config_simultaneous_hand_poses_spec.csv')
    config_rep_file = os.path.join(config_folder, 'config_simultaneous_hand_poses_rep_spec.csv')
    create_swipe_multiple_representations(base_aandb_spec, config_file, config_rep_file, 'AandB', counter=4)
    
    # print(f"\n\n#############################################################")
    # print(f"########   Creating MimicHandPose representations   #########")
    # print(f"#############################################################")
    # create_mimic_hand_pose_representations()
    
    # Delete all the folders except the smartwatch experiment folder
    shutil.rmtree(hand_poses_folder)
    shutil.rmtree(representations_folder)
    shutil.rmtree(mappings_training_folder)
    shutil.rmtree(mappings_experiment_folder)  
    
    # Delete the temp_config_file
    os.remove(temp_config_file)