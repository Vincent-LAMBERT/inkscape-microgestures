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

from microrep.export_hand_poses.configuration_file import (
    compute_default_hand_poses, get_hand_poses)

sys.path.append('/usr/share/inkscape/extensions')
import copy
import itertools
import logging
import os
import shutil
import subprocess
import tempfile

import inkex
from lxml import etree

import microrep.core.export as ex
import microrep.core.ref_and_specs as rf
import microrep.core.utils as u

######################################################################################################################

class ExportHandPoses(inkex.Effect):
    """ The core logic of exporting combinations of layers as images."""

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpg|pdf]')
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to define the hand poses")
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image")
        self.arg_parser.add_argument("--markers", type=inkex.Boolean, dest="markers", default=False, help="Show or hide markers on the exported image")
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Print debug messages as warnings")
        self.arg_parser.add_argument("--dry", type=inkex.Boolean, dest="dry", default=False, help="Don't actually do all of the exports")
    
    def get_label_from_hand_pose(self, orient, hand_pose, logit):
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

    def effect(self):
        """
        Export all combinations of layers corresponding to the given configuration
        This allows to generate all the possible hand poses
        """
        logit = logging.warning if self.options.debug else logging.info
        logit(f"Options: {str(self.options)}")
        
        # Make the families layer invisible
        families_layer = self.document.xpath('//svg:g[@inkscape:label="Families"]', namespaces=inkex.NSS)[0]
        families_layer.set('style', 'display:none')
    
        layer_refs = rf.get_layer_refs(self.document, visible_only=False, logit=logit)        
        wrist_orientation_layer_refs = rf.get_wrist_orientation_layer_refs(layer_refs, logit)

        hand_poses = get_hand_poses(self.options.config, logit)

        # Get layer corresponding to finger and status in layers
        finger_layer_refs = rf.get_finger_pose_layer_refs(layer_refs, logit)

        hide_orient_layers(wrist_orientation_layer_refs, logit)
        hide_finger_layers(finger_layer_refs, logit)
        if not self.options.markers :
            marker_layer_refs = rf.get_marker_layer_refs(layer_refs, logit)
            rf.hide_marker_layers(marker_layer_refs, logit)
        
        count=1  # counter to break on 5 first outputs
        for wrist_orientation in hand_poses.keys() :
            poses = hand_poses[wrist_orientation]
            
            # Only shows the layer with the right wrist_orientation
            # logit("\n\nWrist orientation : "+wrist_orientation)
            update_show_hide_orient(wrist_orientation_layer_refs, wrist_orientation, logit)

            # logit the display attributes of the layers
            # for orient in wrist_orientation_layer_refs :
            #     logit(f"{orient} : {wrist_orientation_layer_refs[orient].source.attrib['style']}")
            
            count = self.export_hand_poses(wrist_orientation, poses, finger_layer_refs[wrist_orientation], count, logit)
            
        show_orient_front_layer(wrist_orientation_layer_refs, logit)
        show_finger_up_layers(finger_layer_refs, logit)
        
        if not self.options.markers :
            rf.show_marker_layers(marker_layer_refs, logit)
    
    def export_hand_poses(self, orient, poses, finger_layer_refs, count, logit):
        """
        Export the hand poses for the given wrist orientation
        """
        for hand_pose in poses:
            update_show_hide_hand_pose(finger_layer_refs, hand_pose, logit)

            if self.options.dry:
                logit(f"Skipping because --dry was specified")
                continue

            label = self.get_label_from_hand_pose(orient, hand_pose, logit)
            new_document = ex.special_deepcopy(self.document)
            new_document = remove_invisible_layers_for_export(new_document, logit)
            ex.export(new_document, f"{label}", self.options, logit)
            
            count+=1
        return count

###### UPDATES THE HAND POSE ######

def update_show_hide_orient(orient_layer_refs, orient, logit) :
    """
    Show the right wrist orientation layer and hide the others
    """
    # logit(f"Update show hide (orient) : ({orient})")

    for wrist_orient, layer_ref in orient_layer_refs.items() :
        if wrist_orient == orient :
            layer_ref.show_layer()
        else :
            layer_ref.hide_layer()
    
def update_show_hide_hand_pose(finger_layer_refs, hand_pose, logit) :
    """
    Show the right hand pose
    """
    # logit(f"Update show hide hand_pose : ({hand_pose})")  
        
    for finger, status_layer_refs in finger_layer_refs.items() :
        for status, layer_ref in status_layer_refs.items() :
            if (finger, status) in hand_pose :
                layer_ref.show_layer()
            else :
                layer_ref.hide_layer()                    

def show_orient_front_layer(wrist_orientation_layer_refs, logit) :
    """
    Show the front wrist orientation layers
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
    
###### CLEAN DOCUMENT FOR EXPORT ######
            
def remove_invisible_layers_for_export(new_document, logit):
    """
    Remove the invisible layers with attribute 'mgrep-wrist-orientation' from each export
    """
    layer_refs = rf.get_layer_refs(new_document, visible_only=False, logit=None)
    wrist_orientation_layer_refs = rf.get_wrist_orientation_layer_refs(layer_refs, logit=None)
    
    for wrist_orientation in wrist_orientation_layer_refs :
        layer_ref = wrist_orientation_layer_refs[wrist_orientation]
        if layer_ref.is_visible() :
            remove_invisible_fingers_in_children(layer_ref, logit)
        else :
            parent = layer_ref.source.getparent()
            parent.remove(layer_ref.source)
    
    return new_document

def remove_invisible_fingers_in_children(layer_ref, logit) :
    """
    Remove the invisible fingers with attribute FingerStatusExportSpec.ATTR_ID from each children
    """
    for child_ref in layer_ref.children :
        remove_invisible_fingers_in_children(child_ref, logit)     
            
        if child_ref.has_valid_finger_status_export_spec() :
            if not child_ref.is_visible() and not child_ref.has_valid_marker_export_spec() :
                parent = child_ref.source.getparent()
                parent.remove(child_ref.source)
            else :
                child_ref.source.attrib.pop(rf.FingerStatusExportSpec.ATTR_ID, None)
            
######################################################################################################################

def _main():
    effect = ExportHandPoses()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#######################################################################################################################
