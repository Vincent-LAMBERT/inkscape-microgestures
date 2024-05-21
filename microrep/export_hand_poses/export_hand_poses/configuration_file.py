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

import itertools
import csv
import logging
import os
import random
import sys

import microrep.core.utils as u

#######################################################################################################################

def compute_default_hand_poses(multi_link_combo=True, simple_link_combo=True) :
    """
    Return the hand poses corresponding to the default configuration
    """
    hand_poses = {}

    for wrist_orientation in u.WRIST_ORIENTATIONS:
        accepted_combinations = compute_accepted_combinations(wrist_orientation, multi_link_combo, simple_link_combo)
        hand_poses[wrist_orientation] = accepted_combinations
    
    return hand_poses

def compute_accepted_combinations(wrist_orientation, multi_link_combo=True, simple_link_combo=True) :
    # Compute all possible combinations of finger other than the thumb and status
    # Compute all possible finger statuses
    orientation_statuses = itertools.product(u.ORIENTATION_STATUSES[wrist_orientation], 
                                    repeat=len(u.FINGERS_WITH_THUMB))
    finger_accepted_combinations = [[(finger, status) for finger,status in zip(u.FINGERS_WITH_THUMB,statuses)] for statuses in orientation_statuses]
    
    # # Remove unaccepted finger combinations
    finger_accepted_combinations = [combination for combination in finger_accepted_combinations if all([status in u.ACCEPTED_STATUSES[finger] for finger,status in combination])]
    
    # Handle multi-links combinations if not three side fingers have the same multi-link status
    new_finger_accepted_combinations = []
    for combination in finger_accepted_combinations :
        if u.has_multi_joints(combination) :
            if multi_link_combo and u.has_valid_multi_joints(combination) :
                new_finger_accepted_combinations.append(combination)
        else :
            new_finger_accepted_combinations.append(combination)
    finger_accepted_combinations = new_finger_accepted_combinations
    
    # Handle add-link and abd-link combinations
    # If a finger is a add-link, then the last side finger must be a abd-link
    new_finger_accepted_combinations = []
    for combination in finger_accepted_combinations :
        if u.has_add_or_abd_joints(combination) :
            if simple_link_combo and u.has_valid_add_and_abd_joints(combination) :
                new_finger_accepted_combinations.append(combination)
        else :
            new_finger_accepted_combinations.append(combination)
    finger_accepted_combinations = new_finger_accepted_combinations

    return finger_accepted_combinations
    
    # Combine with the thumb states as one of the fingers
    # We would combine the thumb with the finger combinations with every thumb hover or touch
    # context if we needed to with the following line
    # accepted_combinations = [[x[0], x[1][0],x[1][1],x[1][2],x[1][3]]  for x in itertools.product(*[thumb_accepted_combinations, finger_accepted_combinations])]
    # However, we only want the thumb to be in the opened state except for the case where every finger is down
    # That is why we compure the following lines
    # at_least_one_up = [[x[0], x[1][0],x[1][1],x[1][2],x[1][3]]  for x in itertools.product(*[[(u.THUMB, u.UP)], finger_accepted_combinations]) if not all([status == u.DOWN for finger,status in x[1]])]
    # all_closed = [[x[0], x[1][0],x[1][1],x[1][2],x[1][3]]  for x in itertools.product(*[[(u.THUMB, u.DOWN)], finger_accepted_combinations]) if all([status == u.DOWN for finger,status in x[1]])]
    # accepted_combinations = at_least_one_up + all_closed
    
    # return accepted_combinations

def get_hand_poses(file_path, logit=logging.info) :
    """
    Return the hand poses corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_hand_poses()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_hand_poses_from_file(file_path, logit)

def get_hand_poses_from_file(file_path, logit=logging.info) :
    """
    Return the hand poses corresponding to the given configuration file
    """
    hand_poses = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\n')
        for row in reader:
            wrist_orientation = u.get_wrist_orientation_name(row[0].split('_')[0])
            if wrist_orientation not in hand_poses :
                hand_poses[wrist_orientation] = []
            hand_poses[wrist_orientation].append(get_hand_poses_from_row(row, logit))
    
    return hand_poses

def get_hand_poses_from_row(row, logit) :
    """
    Return the hand poses corresponding to the given row
    """
    hand_poses = []
    for hand_pose in row :
        fingers = hand_pose.split('_')[1:][0]
        logit(fingers)
        for i, finger in enumerate(u.FINGERS_WITH_THUMB) :
            status = u.get_status_name(fingers[i])
            hand_poses.append((finger, status))
    return hand_poses

#######################################################################################################################

def create_configuration_file(hand_poses, file_path="./configuration/config_export_hand_poses.csv") :
    """
    Creates the configuration file for the hand poses
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))     
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for wrist_orientation, poses in hand_poses.items():
            prefix = u.get_wrist_orientation_nickname(wrist_orientation) + "_"
            for pose in poses:
                hand_pose = ""
                for finger in u.FINGERS_WITH_THUMB:
                    status = get_status(finger, pose)
                    hand_pose += u.get_status_nickname(status)
                writer.writerow([prefix + hand_pose])

def get_status(finger, pose) :
    for f, s in pose :
        if f == finger :
            return s
    raise ValueError(f"The finger {finger} is not in the pose {pose}")

#######################################################################################################################

def _main():
    hand_poses = compute_default_hand_poses()
    if len(sys.argv) > 1 :
        create_configuration_file(hand_poses, sys.argv[1])
    else :
        create_configuration_file(hand_poses)

if __name__ == "__main__":
    _main()

#######################################################################################################################