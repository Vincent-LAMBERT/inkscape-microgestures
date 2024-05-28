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

import sys

from microrep.export_hand_poses.export_hand_poses.configuration_file import compute_default_hand_poses, get_hand_poses
sys.path.append('/usr/share/inkscape/extensions')
import inkex
import os
import subprocess
import tempfile
import shutil
import copy
from lxml import etree
import logging
import itertools
import microrep.core.ref_and_specs as rf
import microrep.core.utils as u
import microrep.core.export as ex

######################################################################################################################

class ExportHandPoses(inkex.Effect):
    """ The core logic of exporting combinations of layers as images."""

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='jpeg', 
                                     help='Exported file type. One of [png|jpeg]')
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to define the hand poses")
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image")
        self.arg_parser.add_argument("--ascii", type=inkex.Boolean, dest="ascii", default=False, 
                                     help="If true, removes non-ascii characters from layer names during export")
        self.arg_parser.add_argument("--lower", type=inkex.Boolean, dest="lower", default=False, 
                                     help="If true, foces the final file name to be lowercase")
        self.arg_parser.add_argument("--multi", type=inkex.Boolean, dest="multi", default=False, 
                                     help="Includes hand poses with 3 or more fingers linked")
        self.arg_parser.add_argument("--simple", type=inkex.Boolean, dest="simple", default=False, 
                                     help="Includes hand poses with 2 fingers linked")
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Print debug messages as warnings")
        self.arg_parser.add_argument("--five", type=inkex.Boolean, dest="five", default=False, help='Stop after processing five combination')
        self.arg_parser.add_argument("--dry", type=inkex.Boolean, dest="dry", default=False, help="Don't actually do all of the exports")
    
    def get_label_from_hand_pose(self, orient, hand_pose, logit):
        # Has as input a hand pose of the form [(finger, status), (finger, status), ...]
        # Returns a string of the form "finger1_status1_finger2_status2_..."
        label = u.get_wrist_orientation_nickname(orient)+"_"
        for finger, status in hand_pose:
            finger_nick = finger[0].capitalize()
            status_nick = u.get_status_nickname(status).lower()
            label += finger_nick+status_nick+"-"
        label = label[:-1]
        return label

    def effect(self):
        logit = logging.warning if self.options.debug else logging.info
        logit(f"Options: {str(self.options)}")
    
        layer_refs = rf.get_layer_refs(self.document, visible_only=False, logit=logit)
        wrist_orientation_layer_refs = rf.get_wrist_orientation_layer_refs(layer_refs, logit)

        hand_poses = get_hand_poses(self.options.config, logit)
        logit(f"Hand poses: {str(hand_poses)}")

        # Get layer corresponding to finger and status in layers
        finger_layer_refs = rf.get_finger_pose_layer_refs(layer_refs, logit)

        hide_orient_layers(wrist_orientation_layer_refs, logit)
        hide_finger_layers(finger_layer_refs, logit)
        
        count=1  # counter to break on 5 first outputs
        for wrist_orientation in hand_poses.keys() :
            poses = hand_poses[wrist_orientation]

            # Only shows the layer with the right wrist_orientation
            logit("Wrist orientation : "+wrist_orientation)
            update_show_hide_orient(wrist_orientation_layer_refs, wrist_orientation, logit)

            count = self.export_hand_poses(wrist_orientation, poses, finger_layer_refs[wrist_orientation], count, logit)
            if self.options.five and count==5:
                break
            
        show_orient_front_layer(wrist_orientation_layer_refs, logit)
        show_finger_up_layers(finger_layer_refs, logit)
    
    def export_hand_poses(self, orient, poses, finger_layer_refs, count, logit):
        for hand_pose in poses:
            update_show_hide_hand_pose(finger_layer_refs, hand_pose, logit)

            if self.options.dry:
                logit(f"Skipping because --dry was specified")
                continue

            label = self.get_label_from_hand_pose(orient, hand_pose, logit)
            ex.export(self.document, f"{label}", self.options, logit)
            # Break on 5 first outputs for debug purposes
            if self.options.five and count==5:
                return count
            count+=1
        return count
            
def update_show_hide_orient(orient_layer_refs, orient, logit) :
    logit(f"Update show hide (orient) : ({orient})")

    for wrist_orient, layer_ref in orient_layer_refs.items() :
        if wrist_orient == orient :
            layer_ref.show_layer()
        else :
            layer_ref.hide_layer()
    
def update_show_hide_hand_pose(finger_layer_refs, hand_pose, logit) :
    logit(f"\n\n\nUpdate show hide hand_pose : ({hand_pose})")           
        
    for finger, status_layer_refs in finger_layer_refs.items() :
        for status, layer_ref in status_layer_refs.items() :
            if (finger, status) in hand_pose :
                layer_ref.show_layer()
            else :
                layer_ref.hide_layer()                    

def show_orient_front_layer(wrist_orientation_layer_refs, logit) :
    """
    Show the wrist orientation layers
    """
    for wrist_orientation in wrist_orientation_layer_refs :
        layer = wrist_orientation_layer_refs[wrist_orientation]
        if wrist_orientation == "front" :
            layer.source.attrib['style'] = 'display:inline'
        else :
            layer.source.attrib['style'] = 'display:none'

def hide_orient_layers(wrist_orientation_layer_refs, logit) :
    """
    Hide the wrist orientation layers
    """
    for wrist_orientation in wrist_orientation_layer_refs :
        layer = wrist_orientation_layer_refs[wrist_orientation]
        layer.source.attrib['style'] = 'display:none'

def show_finger_up_layers(finger_status_layer_refs, logit) :
    """
    Show the finger layers
    """
    for wrist_orientation in finger_status_layer_refs :
        for finger in finger_status_layer_refs[wrist_orientation] :
            for status in finger_status_layer_refs[wrist_orientation][finger] :
                layer = finger_status_layer_refs[wrist_orientation][finger][status]
                if status == "up" :
                    layer.source.attrib['style'] = 'display:inline'
                else :
                    layer.source.attrib['style'] = 'display:none'

def hide_finger_layers(finger_status_layer_refs, logit) :
    """
    Hide the finger layers
    """
    for wrist_orientation in finger_status_layer_refs :
        for finger in finger_status_layer_refs[wrist_orientation] :
            for status in finger_status_layer_refs[wrist_orientation][finger] :
                layer = finger_status_layer_refs[wrist_orientation][finger][status]
                layer.source.attrib['style'] = 'display:none'

######################################################################################################################

def _main():
    effect = ExportHandPoses()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#######################################################################################################################
