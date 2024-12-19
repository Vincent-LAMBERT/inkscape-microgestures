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

FAMILIES=["A&B", "MaS"]

LEFT = "left"
RIGHT = "right"
BACK = "back"
FRONT = "front"
BACK_LEFT = "back-left"
BACK_RIGHT = "back-right"
FRONT_LEFT = "front-left"
FRONT_RIGHT = "front-right"
WRIST_ORIENTATIONS = [LEFT, RIGHT, BACK, FRONT, BACK_LEFT, BACK_RIGHT, FRONT_LEFT, FRONT_RIGHT]

def get_wrist_orientation_nickname(wrist_orientation) :
    return ''.join([str(x[0]).capitalize() for x in wrist_orientation.split('-')])

def get_wrist_orientation_name(wrist_orientation_nickname) :
    for wrist_orientation in WRIST_ORIENTATIONS :
        if get_wrist_orientation_nickname(wrist_orientation) == wrist_orientation_nickname :
            return wrist_orientation

THUMB="thumb"
INDEX="index"
MIDDLE="middle"
RING="ring"
PINKY="pinky"
FINGERS = [INDEX, MIDDLE, RING, PINKY]
FINGERS_WITH_THUMB = [THUMB, INDEX, MIDDLE, RING, PINKY]
INDEX_MIDDLE=INDEX+"-"+MIDDLE
MIDDLE_RING=MIDDLE+"-"+RING
RING_PINKY=RING+"-"+PINKY
INDEX_MIDDLE_RING=INDEX+"-"+MIDDLE+"-"+RING
MIDDLE_RING_PINKY=MIDDLE+"-"+RING+"-"+PINKY
INDEX_MIDDLE_RING_PINKY=INDEX+"-"+MIDDLE+"-"+RING+"-"+PINKY
FINGERS_COMBOS=[INDEX_MIDDLE, MIDDLE_RING, RING_PINKY]+[INDEX_MIDDLE_RING, MIDDLE_RING_PINKY]+[INDEX_MIDDLE_RING_PINKY]

UP = "up"
CLOSE = "close"
FLEX = "flex"
ADDUCTION = "adduction"
ABDUCTION = "abduction"
COMPLEX = "complex"
FINGER_STATUSES = [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX]
ORIENTATION_STATUSES = { LEFT : [UP, CLOSE, FLEX],
                         RIGHT : [UP, CLOSE, FLEX],
                         BACK : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                         FRONT : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                         BACK_LEFT : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                         BACK_RIGHT : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                         FRONT_LEFT : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                         FRONT_RIGHT : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX]}

def get_finger_nickname(finger) :
    return finger[0].capitalize()

def get_finger_name(finger_nickname) :
    for finger in FINGERS_WITH_THUMB :
        if get_finger_nickname(finger) == finger_nickname :
            return finger

def get_status_nickname(status) :
    if status == COMPLEX:
        return status[-1]
    if status in [ADDUCTION, ABDUCTION] :
        return status[1]
    return status[0]

def get_status_name(status_nickname) :
    for status in FINGER_STATUSES :
        if get_status_nickname(status) == status_nickname :
            return status

ACCEPTED_STATUSES = { THUMB : [UP],
                      INDEX : [UP, CLOSE, FLEX, ADDUCTION, COMPLEX],
                      MIDDLE : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                      RING : [UP, CLOSE, FLEX, ADDUCTION, ABDUCTION, COMPLEX],
                      PINKY : [UP, CLOSE, FLEX, ABDUCTION, COMPLEX] }

PROXIMATE_FINGERS = {   THUMB : [],
                        INDEX : [MIDDLE],
                        MIDDLE : [INDEX, RING],
                        RING : [MIDDLE, PINKY],
                        PINKY : [RING]  }

ACCEPTED_LINKS = [  {ADDUCTION : INDEX, ABDUCTION : MIDDLE},
                    {ADDUCTION : MIDDLE, ABDUCTION : RING},
                    {ADDUCTION : RING, ABDUCTION : PINKY} ]


def has_multi_joints(combination) :
    return any([status == COMPLEX for finger,status in combination])

def has_add_or_abd_joints(combination) :
    return any([status == ADDUCTION for finger,status in combination]) or any([status == ABDUCTION for finger,status in combination])

def has_valid_multi_joints(combination) :
    # If the thumb is a complex, return False
    if any([finger == THUMB and status == COMPLEX for finger,status in combination]) :
        return False
    # If there is less than 3 multi-links, return False
    if len([status for finger,status in combination if status == COMPLEX]) < 3 :
        return False
    # If both the middle and the ring are multi-links, its true, otherwise return False
    if any([finger == MIDDLE and status == COMPLEX for finger,status in combination]) and any([finger == RING and status == COMPLEX for finger,status in combination]) :
        return True
    return False

def has_valid_add_and_abd_joints(combination) :
    # Check if there is an equal number of add-links and abd-links
    if len([status for finger,status in combination if status == ADDUCTION]) != len([status for finger,status in combination if status == ABDUCTION]) :
        return False
    # At this state there is a abduction for each adduction
    # Fetch all add-links and abd-links as a list of couples
    add_fingers = [finger for finger,status in combination if status == ADDUCTION]
    abd_fingers = [finger for finger,status in combination if status == ABDUCTION]    
    
    for add_finger in add_fingers :
        # Check if one of the proximate fingers of the add_finger has a abduction
        proximate_fingers_with_abd_link = intersect(PROXIMATE_FINGERS[add_finger], abd_fingers)
        if proximate_fingers_with_abd_link==[] :
            return False
        # If its the case, still check if the link is accepted
        # Get the adb-link with the adduction being the add_finger in the accepted links
        i = 0
        while ACCEPTED_LINKS[i][ADDUCTION] != add_finger :
            i+=1
        # Check if the abduction is the one accepted
        if ACCEPTED_LINKS[i][ABDUCTION] not in proximate_fingers_with_abd_link :
            return False
    return True

def intersect(list1, list2):
    set1 = set(list1)
    set2 = set(list2)

    set3 = set1 & set2
    return list(set3)


#################################################################
####################    MICROGESTURES    ########################
#################################################################

DOWN = "down"

TAP = "tap"
SWIPE = "swipe"
HOLD = "hold"
TIP = "tip"
MIDDLE = "middle"
BASE = "base"
NAIL = "nail"
SIDE = "side"
MICROGESTURES = [TAP, HOLD, SWIPE]
TAP_CHARACTERISTICS = [SIDE, TIP, MIDDLE, BASE, NAIL]
SWIPE_CHARACTERISTICS = [UP, DOWN, RIGHT, LEFT]
HOLD_CHARACTERISTICS = [TIP, MIDDLE, BASE, NAIL, SIDE]
MICROGESTURE_CHARACTERISTICS = { TAP : TAP_CHARACTERISTICS,
                                 SWIPE : SWIPE_CHARACTERISTICS,
                                 HOLD : HOLD_CHARACTERISTICS}

ACTUATOR="actuator"
RECEIVER="receiver"
TRAJECTORY="trajectory"
ELEMENTS = [ACTUATOR, RECEIVER, TRAJECTORY]
TAP_ELEMENTS = [TRAJECTORY, ACTUATOR, RECEIVER]
SWIPE_ELEMENTS = [TRAJECTORY, ACTUATOR]
HOLD_ELEMENTS = [TRAJECTORY, ACTUATOR, RECEIVER]
MG_ELEMENTS = { TAP : TAP_ELEMENTS,
                SWIPE : SWIPE_ELEMENTS,
                HOLD : HOLD_ELEMENTS}
PUNCTUAL = "punctual"
PATH = "path"
ELEMENT_SVG_TYPE_CORRESPONDANCE = { ACTUATOR : PUNCTUAL,
                                    RECEIVER : PUNCTUAL,
                                    TRAJECTORY : PATH}
TRAJ_START="traj-start"
TRAJ_END="traj-end"
MARKER_TYPES_CORRESPONDANCE = { TAP : [TRAJ_START, TRAJ_END, ACTUATOR, RECEIVER],
                                SWIPE : [TRAJ_START, TRAJ_END, ACTUATOR],
                                HOLD : [TRAJ_START, TRAJ_END, ACTUATOR, RECEIVER]}
MARKER_TYPES=[TRAJ_START, TRAJ_END, ACTUATOR, RECEIVER]

COORDINATES = "coordinates"
CIRCLE_RADIUS = "r"

PNG="png"
JPG="jpg"
PDF="pdf"
SVG="svg"

START = "start"
END = "end"
CONTROL_1 = "control1"
CONTROL_2 = "control2"


MREP_PATH_ELEMENT = 'mgrep-path-element'
DESIGN="design"
TRACE="trace"
TRACE_START_BOUND="trace-start-bound"
TRACE_END_BOUND="trace-end-bound"
COMMAND="command"
ICON_COMMAND="icon-command"
PATH_BASED_TYPES = [DESIGN, TRACE]
CIRCLE_BASED_TYPES = [TRACE_START_BOUND, TRACE_END_BOUND, COMMAND]


SWIPE_UP = "swipe-up"
SWIPE_DOWN = "swipe-down"
CLUSTERED_MARKER = "legended-marker"
ICON_TYPES = [TAP, SWIPE_UP, SWIPE_DOWN, HOLD, CLUSTERED_MARKER]

BELOW = "below"
ABOVE = "above"
DIRECTIONS = [LEFT, RIGHT, BELOW, ABOVE]



NAME = "name"
COMBINATION = "combination"
MAPPING = "mapping"

START = 'start'
END = 'end'
CONTROL_1 = 'control1'
CONTROL_2 = 'control2'
RADIUS = 'radius'
TO = 'to'

STROKE = "stroke"
FILL = "fill"
COLOR_BASED_STYLES = [FILL, STROKE]
RED = 'red'
BLUE = 'blue'
GREEN = 'green'
COLORS = { RED : "#FF0000",
           BLUE : "#0000FF",
           GREEN : "#00FF00"}

STROKE_WIDTH = "stroke-width"
PATH_SCALE = "path-scale"
THIN = "thin"
MEDIUM = "medium"
THICK = "thick"
SIZES = { THIN : 0.75,
          MEDIUM : 1,
          THICK : 1.5}

STYLES = COLOR_BASED_STYLES + [STROKE_WIDTH]
STYLE_CHARACTERISTICS = { STROKE : COLORS,
                          FILL : COLORS,
                          STROKE_WIDTH : SIZES}


DEFAULT_CATEGORIES = [["bat", "camel", "cat", "dinosaur", "dog", "dolphin", "duck", "fish", "frog", "penguin", "pigeon", "zebra"],
                      ["apple", "banana", "cherry", "grapes", "kiwi", "lemon", "peach", "pear", "pineapple", "prune", "strawberry", "watermelon"],
                      ["artichoke", "broccoli", "carrot", "corn", "cucumber", "pumpkin", "garlic", "lettuce", "mushroom", "onion", "pepper", "potato"],
                      ["chair", "clock", "enveloppe", "keyboard", "mouse", "paperclip", "pencil", "printer", "stamp", "stapler", "telephone", "trash"], 
                      ["boot", "bowtie", "button", "coat", "shirt", "gloves", "hat", "skirt", "socks", "sweater", "tshirt", "trousers"],
                      ["basketball", "baseball", "bowling", "cards", "chess", "darts", "dice", "hockey", "karate", "pool", "rubikscube", "tennis"]]


BANANA = "banana"
PINEAPPLE = "pineapple"
CHERRY = "cherry"
KIWI = "kiwi"
STRAWBERRY = "strawberry"
PRUNE = "prune"
WATERMELON = "watermelon"
COMMANDS = [BANANA, PINEAPPLE, CHERRY, KIWI, STRAWBERRY, PRUNE, WATERMELON]
        
COLLIDE_WITH_COMMANDS = "collide_with_commands"
COLLIDE_WITH_DESIGNS = "collide_with_designs"
COLLIDE_WITH_HAND = "collide_with_hand"

START = "start"
CENTER = "center"
END = "end"
TEXT_ALIGNS = {RIGHT : START, LEFT : END, BELOW : CENTER, ABOVE : CENTER}

MIDDLE = "middle"
TEXT_ANCHORS = {RIGHT : START, LEFT : END, BELOW : MIDDLE, ABOVE : MIDDLE}

OPPOSITE_ANCHORS = {RIGHT : LEFT, LEFT : RIGHT, BELOW : ABOVE, ABOVE : BELOW}

CENTROID="centroid"
TEMPLATE="template"
LEGEND_TYPES = [LEFT, RIGHT]


#######################################################################################################################

def get_combination_name(combination) :
    """
    Return the name of the given combination
    Each of the given combination must have the form 
    ((finger1, microgesture1, characteristic1), (finger2, microgesture2, ...), ...).
    Each microgesture would be described by its first capitalized letter and 
    each characteristic by its first minimized letter
    
    Example: (('index', 'tap', 'tip'), ('middle', 'swipe','up')) combination
    would be named iTt-mSu
    """
    name = ""
    for representation in combination :
        name += representation[0][0].lower() + representation[1][0].upper() + representation[2][0].lower() + "-"
    return name[:-1]

def get_combination_from_name(name) :
    """
    Return the combination from the given name
    The given name must have the form 
    ((finger1, microgesture1, characteristic1), (finger2, microgesture2, ...), ...).
    Each microgesture would be described by its first capitalized letter and 
    each characteristic by its first minimized letter
    
    Example: Tt-Su name would return (('index', 'tap', 'tip'), ('middle', 'swipe','up')) combination
    """
    combination = []
    equivalence = {"fingers" : {"i" : "index", "m" : "middle", "r" : "ring", "p" : "pinky"},
                    "microgestures" : {"T" : "tap", "S" : "swipe", "H" : "hold"},
                    "characteristics" : {"t" : "tip", "m" : "middle", "b" : "base", "u" : "up", "d" : "down"}}
    combination_name = name.split("_")[-1]
    for representation in combination_name.split("-") :
        try :
            finger = equivalence["fingers"][representation[0]]
            microgesture = equivalence["microgestures"][representation[1]]
            characteristic = equivalence["characteristics"][representation[2]]
            combination.append((finger, microgesture, characteristic))
        except KeyError :
            continue
    return combination

def get_fmc_combination(combinations) :
    """
    Return the (finger, microgestures, characteristic) unique tuples from the given combinations
    """
    fmcs = []
    for combination in combinations :
        for fmc in combination :
            if fmcs not in fmcs :
                fmcs.append(fmc)
    # Filter the fmcs to keep distinct fmcs with the SAME ORDER
    filtered_fmcs = []
    for fmc in fmcs :
        if fmc not in filtered_fmcs :
            filtered_fmcs.append(fmc)
    return fmcs
      
def get_most_proximate_finger_and_charac_for_tap_raw(fmc_combinations, logit) :
    for p_f in FINGERS :
        for p_c in TAP_CHARACTERISTICS :
            for finger, mg, charac in fmc_combinations :
                if finger==p_f and mg==TAP and charac==p_c :
                    return p_f, p_c
    return None, None

def get_most_proximate_finger_and_charac_for_tap(fmc_combinations, logit) :
    """
    Get the finger and characteristic that are closer to the thumb in the fmc_combinations
    Don't send any if other fingers exist and would cross the arrow trajectory
    """
    f, c = get_most_proximate_finger_and_charac_for_tap_raw(fmc_combinations, logit)
    logit(f"f: {f}, c: {c}")
                    
    if f in [INDEX, MIDDLE]:
        return f, c
    elif f in [RING, PINKY]:
        # Check if there is a SWIPE involving the MIDDLE finger AND that the tap was done on the tip or the side of the finger
        # If so, the tap arrow would cross the swipe arrow and should not be displayed
        if c in [TIP, SIDE]:
            for finger, mg, charac in fmc_combinations :
                if MIDDLE in finger and mg==SWIPE :
                    return None, None
        return f, c

    return None, None