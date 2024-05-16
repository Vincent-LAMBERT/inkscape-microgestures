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
sys.path.append('/usr/share/inkscape/extensions')
import inkex

import copy
import logging
import os
import tempfile
import subprocess
import svg.path
import numpy as np
from lxml import etree

from microrep.complete_occlusion_adaptation.complete_occlusion_adaptation.configuration_file import *
import microrep.core.utils as u
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.scale_mg_rep as sc
import microrep.core.export as ex

#####################################################################

class CompleteOcclusionAdaptation(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpeg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument('--strategy', type=str, dest='strategy', default='default', 
                                     help='Non spatial strategy used. One of [default|brightness|text]')
        self.arg_parser.add_argument('--integration', type=str, dest='integration', default='default', 
                                     help='Labels integrated in a legend or placed by default next to the icon. One of [default|integration]')
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
    
    def effect(self):
        """
        This is the core of the extension
        It gathers all layers, puts all families elements in a Nx4 matrix
        and compute the representations  for each one of them 
        according to the markers types and position  
        """
        logit = logging.warning if self.options.debug else logging.info
        logit(f"Running Python interpreter: {sys.executable}")
        logit(f"Options: {str(self.options)}")

        # Set the svg name
        self.svg_name = ex.get_svg_name(self.options, self.svg)
        
        # Get the layers
        layer_refs = rf.get_layer_refs(self.document, False, logit)
        # Filter the visible layers 
        visible_layer_refs = [layer_ref for layer_ref in layer_refs if layer_ref.source.is_visible()]
        # Filter by microgesture
        tap_layer_refs = [layer_ref for layer_ref in filter_layer_ref_by_mg(visible_layer_refs, "tap", logit)]
        hold_layer_refs = [layer_ref for layer_ref in filter_layer_ref_by_mg(visible_layer_refs, "hold", logit)]
        # Get tap commands 
        tap_commands = get_commands(tap_layer_refs)
        # Get hold commands
        hold_commands = get_commands(hold_layer_refs)
        
        strategy = self.options.strategy
        integration = self.options.integration
        family_name = self.get_active_family()
        
        match strategy:
            case "default" :
                if family_name == "AandB" :
                    modify_default_AandB(tap_commands, hold_commands, logit)
                else :
                    modify_default_MaS(tap_commands, hold_commands, logit)
            case "brightness" :
                tap_designs = get_designs(tap_layer_refs)
                hold_designs = get_designs(hold_layer_refs)
                tap_minicons = create_brightness_minicons(tap_designs, u.TAP, family_name, logit)
                hold_minicons = create_brightness_minicons(hold_designs, u.HOLD, family_name, logit)
                if integration == "default" :
                    modify_brightness_default(tap_commands, hold_commands, tap_minicons, hold_minicons, logit)
                else :
                    modify_brightness_integration(tap_commands, hold_commands, tap_minicons, hold_minicons, logit)
            case "text" :
                if integration == "default" :
                    modify_text_default(tap_commands, hold_commands, logit)
                else :
                    modify_text_integration(tap_commands, hold_commands, logit)
        
        logit(f"Exporting to {self.svg_name}")
        ex.export(self.document, self.svg_name, self.options, logit)
                    
    def get_active_family(self) :
        """
        Get the active family
        It corresponds to the family of the first sublayer of the Design layer which is visible
        """
        # Get all Design layer sublayers
        design_layer = self.document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)[0]
        design_layer_sublayers = design_layer.getchildren()
        # Get the first visible sublayer
        for sublayer in design_layer_sublayers :
            if sublayer.is_visible() :
                # Get the family of the sublayer
                # It corresponds to the first element of the mgrep-family-layer attribute
                return sublayer.get("mgrep-family-layer").split(",")[0].replace(" ", "")

#####################################################################

def scale_child(layer_ref, child, scaling, logit=logging.info) :
    """
    Scale the child
    """
    # Get the initial path
    initial_path = layer_ref.non_layer_children_initial_path[child.get("id")]
    # Get the bound zones
    bound_zones = sc.get_bound_zones(layer_ref.source)
    # Scale the path
    if bound_zones!=[] and scaling!=1.0 :
        scaled_path = sc.scale_path(initial_path, bound_zones, scaling, logit)
    else :
        scaled_path = initial_path
    # Set the new path
    child.set("d", scaled_path)

def filter_layer_ref_by_mg(layer_refs, mg_type, logit=logging.info) :
    """
    Filter the layer_refs by microgesture type
    """
    for layer_ref in layer_refs :
        mgrep_microgesture_layer = layer_ref.source.get("mgrep-microgesture-layer")
        if mgrep_microgesture_layer != None :
            mg = mgrep_microgesture_layer.split(",")[1]
            mg = mg.replace(" ", "")
            if mg == mg_type :
                yield layer_ref

def get_commands(layer_refs) :
    """
    Get the commands
    """
    commands = []
    icon_commands = []
    for layer_ref in layer_refs :
        for child in layer_ref.source.getchildren() :
            if child.get("mgrep-path-element") == u.COMMAND :
                commands.append(child)
            elif child.get("mgrep-path-element") == u.ICON_COMMAND :
                icon_commands.append(child)
    if len(icon_commands) == 0 :
        return commands
    else :
        return icon_commands

def get_designs(layer_refs) :
    """
    Get the designs
    """
    designs = []
    for layer_ref in layer_refs :
        for child in layer_ref.source.getchildren() :
            if child.get("mgrep-path-element") == u.COMMAND :
                for child in layer_ref.source.getchildren() :
                    if child.get("mgrep-path-element") == u.DESIGN :
                        designs.append(child)
                        break
    return designs
        
def apply_matrix_to_command(command, matrix, logit=logging.info) :
    """
    Apply the matrix to the command
    """
    path_cx = command.get("cx")
    path_cy = command.get("cy")
    path_r = command.get("r")
    circle_coords = {u.COORDINATES : mg.convert_to_complex(path_cx, path_cy), u.CIRCLE_RADIUS : path_r}    
    circle = mg.apply_matrix_to_circle(circle_coords, [], matrix, logit)
    command.set("cx", str(circle[u.COORDINATES].real))
    command.set("cy", str(circle[u.COORDINATES].imag))

far_far_left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-14, 0]))
far_left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-9, 0]))
far_right_T_matrix = mg.get_translation_matrix_from_vector(np.array([9, 0]))
slight_far_left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-6, 0]))
slight_far_right_T_matrix = mg.get_translation_matrix_from_vector(np.array([6, 0]))
left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-5, 0]))
right_T_matrix = mg.get_translation_matrix_from_vector(np.array([5, 0]))
mini_left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-2, 0]))
mini_right_T_matrix = mg.get_translation_matrix_from_vector(np.array([2, 0]))
slight_left_T_matrix = mg.get_translation_matrix_from_vector(np.array([-3, 0]))
slight_right_T_matrix = mg.get_translation_matrix_from_vector(np.array([3, 0]))
bottom_first_T_matrix = mg.get_translation_matrix_from_vector(np.array([0, 9]))
bottom_second_T_matrix = mg.get_translation_matrix_from_vector(np.array([0, 15]))

####################################################################

AandBTap_minicon_path = "m 98.700771,45.830727 a 1.3424533,1.3424533 0 0 1 -1.342447,1.342453 1.3424533,1.3424533 0 0 1 -1.342453,-1.342453 1.3424533,1.3424533 0 0 1 1.342453,-1.342453 1.3424533,1.3424533 0 0 1 1.342447,1.342453 z"
AandBHold_minicon_path = "m 101.2065,40.667441 a 1.9999995,1.9999995 0 0 1 -2.000002,1.999999 1.9999995,1.9999995 0 0 1 -2,-1.999999 1.9999995,1.9999995 0 0 1 2,-2 1.9999995,1.9999995 0 0 1 2.000002,2 z"
MaSTap_minicon_path = "m 101.2065,40.667441 a 1.9999995,1.9999995 0 0 1 -2.000002,1.999999 1.9999995,1.9999995 0 0 1 -2,-1.999999 1.9999995,1.9999995 0 0 1 2,-2 1.9999995,1.9999995 0 0 1 2.000002,2 z"
MaSHold_minicon_path = "m 97.40376,39.195439 h 3.51677 v 3.516766 h -3.51677 z"

def get_minicon_path(mg, family) :
    """
    Get the minicon path
    """
    if mg == u.TAP :
        if family == "AandB" :
            return AandBTap_minicon_path
        else :
            return MaSTap_minicon_path
    elif mg == u.HOLD :
        if family == "AandB" :
            return AandBHold_minicon_path
        else :
            return MaSHold_minicon_path
    return None

####################################################################

def modify_default_AandB(tap_commands, hold_commands, logit):
    """
    Modify the representation for a default strategy with a default labelling
    """
    # Move the tap commands to the bottom right
    for command in tap_commands :
        apply_matrix_to_command(command, right_T_matrix @ bottom_first_T_matrix, logit)
    # Move the hold commands to the left
    for command in hold_commands :
        apply_matrix_to_command(command, far_left_T_matrix, logit)

def modify_default_MaS(tap_commands, hold_commands, logit=logging.info) :
    """
    Modify the representation for a default strategy with a default labelling
    """
    # Move the tap commands to the right
    for command in tap_commands :
        apply_matrix_to_command(command, far_right_T_matrix, logit)
    # Move the hold commands to the left
    for command in hold_commands :
        apply_matrix_to_command(command, far_left_T_matrix, logit)
        
def create_brightness_minicons(designs, mg, family, logit=logging.info) :
    """
    Create the minicons for a brightness strategy
    """
    minicons = []
    for design in designs :
        # Create a minicon for each design
        minicon = etree.Element(inkex.addNS("path", "svg"))
        minicons.append(minicon)
        minicon.set("d", get_minicon_path(mg, family))
        # Copy design
        minicon.set("style", design.get("style"))
        parent = design.getparent()
        parent.insert(parent.index(design) + 1, minicon)
        
    return minicons

def apply_matrix_to_design(command, design, matrix, logit=logging.info) :
    """
    Apply a matrix to a design
    """
    parsed_path = svg.path.parse_path(design.get("d"))
    centroid = mg.get_center_path(design.get("d"))
    
    # Move centroid to the origin
    origin_T_matrix = mg.get_translation_matrix(centroid, [0, 0])
    # Move centroid to the command centroid
    command_centroid = [float(command.get("cx")), float(command.get("cy"))]
    centroid_T_matrix = mg.get_translation_matrix([0, 0], command_centroid)
    
    parsed_path = mg.apply_matrix_to_path(parsed_path, {}, matrix @ centroid_T_matrix @ origin_T_matrix, logit)
    design.set("d", parsed_path.d())
    centroid = mg.get_center_path(parsed_path.d())
    
    create_legend_marker(design, centroid)
    
def create_legend_marker(design, centroid) :
    """
    Create a legend marker for a design
    """
    
    # Create a circle to have legend markers
    marker = etree.Element(inkex.addNS("circle", "svg"))
    marker.set("mgrep-legend", "special")
    marker.set("cx", str(centroid[0]))
    marker.set("cy", str(centroid[1]))
    
    # Add the marker to the design layer
    parent = design.getparent()
    parent.insert(parent.index(design) + 1, marker)

def modify_brightness_default(tap_commands, hold_commands, tap_minicons, hold_minicons, logit=logging.info) :
    """
    Modify the representation for a brightness strategy with a default labelling
    """
    # Move the tap commands to the bottom left
    for command, design in zip(tap_commands, tap_minicons) :
        apply_matrix_to_command(command, far_left_T_matrix @ bottom_first_T_matrix, logit)
        apply_matrix_to_design(command, design, slight_far_left_T_matrix, logit)
    # Move the hold designs to the bottom right
    for command, design in zip(hold_commands, hold_minicons) :
        apply_matrix_to_command(command, far_left_T_matrix @ bottom_second_T_matrix, logit)
        apply_matrix_to_design(command, design, slight_far_left_T_matrix, logit)
        
def modify_brightness_integration(tap_commands, hold_commands, tap_minicons, hold_minicons, logit=logging.info) :
    """
    Modify the representation for a brightness strategy with an integration labelling
    """
    # Move the tap commands to the bottom right
    for command, design in zip(tap_commands, tap_minicons) :
        apply_matrix_to_command(command, mini_right_T_matrix @ bottom_first_T_matrix, logit)
        apply_matrix_to_design(command, design, slight_far_left_T_matrix, logit)
    # Move the hold designs to the bottom right
    for command, design in zip(hold_commands, hold_minicons) :
        apply_matrix_to_command(command, mini_right_T_matrix @ bottom_second_T_matrix, logit)
        apply_matrix_to_design(command, design, slight_far_left_T_matrix, logit)

def modify_text_default(tap_commands, hold_commands, logit=logging.info) :
    """
    Modify the representation for a text strategy with a default labelling
    """
    # Move the tap commands to the far bottom left
    for command in tap_commands :
        apply_matrix_to_command(command, far_far_left_T_matrix @ bottom_first_T_matrix, logit)
        create_legend_marker(command, [float(command.get("cx")), float(command.get("cy"))])
    # Move the hold commands to the far bottom left
    for command in hold_commands :
        apply_matrix_to_command(command, far_far_left_T_matrix @ bottom_second_T_matrix, logit)
        create_legend_marker(command, [float(command.get("cx")), float(command.get("cy"))])
        
def modify_text_integration(tap_commands, hold_commands, logit=logging.info) :
    """
    Modify the representation for a text strategy with an integration labelling
    """
    # Move the tap commands to the bottom left
    for command in tap_commands :
        apply_matrix_to_command(command, slight_left_T_matrix @ bottom_first_T_matrix, logit)
    # Move the hold commands to the bottom right
    for command in hold_commands :
        apply_matrix_to_command(command, slight_right_T_matrix @ bottom_first_T_matrix, logit)

#####################################################################

def _main():
    effect = CompleteOcclusionAdaptation()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

####################################################################