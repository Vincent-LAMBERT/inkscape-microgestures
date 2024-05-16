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

from lxml import etree
import copy
import svg.path 
import numpy as np
import logging
import os
import tempfile
import subprocess
from inkex.elements import Group

from microrep.add_legend.add_legend.configuration_file import *
import microrep.core.utils as u
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.export as ex

#######################################################################################################################

class AddLegend(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpeg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to define the legends")
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
    
    def effect(self):
        """
        This is the core of the extension
        It gathers all layers, puts all families elements in a Nx4 matrix
        and compute the representations  for each one of them 
        according to the commands types and position  
        """
        logit = logging.warning if self.options.debug else logging.info
        logit(f"Running Python interpreter: {sys.executable}")
        logit(f"Options: {str(self.options)}")

        # Set the svg name
        self.svg_name = ex.get_svg_name(self.options, self.svg)
        
        # Get a dictionnary of the wanted diversified styles with their characteristics
        legends = get_legends(self.options.config, logit)
        
        # Get the commands positions
        layer_refs = rf.get_layer_refs(self.document, False, logit)
        mg_layer_refs = rf.get_mg_layer_refs(layer_refs, logit)
        self.commands_with_positions = rf.get_commands_with_positions(mg_layer_refs, logit)
        self.duplicate_command_icons(mg_layer_refs, logit)
        marker_layer_refs = rf.get_marker_layer_refs(layer_refs, logit)
        markers_positions = rf.get_markers_pos(marker_layer_refs, logit)
        
        # Get the legends references
        dirname = os.path.dirname(__file__)
        self.legend_one_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendOne.svg", logit)[0]
        self.legend_two_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendTwo.svg", logit)[0]
        self.legend_three_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendThree.svg", logit)[0]
        self.legend_four_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendFour.svg", logit)[0]
        self.legend_five_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendFive.svg", logit)[0]
        self.legend_six_ref = self.get_svg_layers_ref(f"{dirname}/Legends/LegendSix.svg", logit)[0]
        
        # Create the legend layer above all the other layers
        self.legend_layer = self.create_legend_layer()
        
        # For the moment we only hande one type of legending per file
        for i, legend in enumerate(legends) :
            finger = legend[0][0]
            mgs = [mg for (finger, mg, charac) in legend]
            characs = [charac for (finger, mg, charac) in legend]
            legend_ref = self.get_legend_ref(len(mgs))
            legend_TRS_matrix = self.create_legend(legend_ref, mgs, characs, markers_positions[finger], u.LEGEND_TYPES[len(legends)-(i+1)], logit)
            self.move_commands_to_legend(legend_ref, finger, mgs, characs, legend_TRS_matrix, logit)
        
        logit(f"Exporting Legended+{self.svg_name}")
        ex.export(self.document, f"Legended+{self.svg_name}", self.options, logit)
        
        self.reset_command_positions(legends, logit)
        self.delete_icon_commands(mg_layer_refs, logit)
        
        # Delete layer with label "Legend"
        self.legend_layer.delete()

#####################################################################
    
    def create_legend_layer(self) :
        """
        Creates the layer that will handle all the legends
        It is placed above all the existing layers to be visible
        """
        legend_layer = Group.new('Legends', is_layer=True)
        # Add legend layer to the document
        self.document.getroot().append(legend_layer)
        return legend_layer

    def get_svg_layers_ref(self, file, logit) -> list:
        """
        Return the layers in the SVG
        """
        document = etree.parse(file)
        return rf.get_layer_refs(document, False, logit)
            
    def reset_command_positions(self, legends, logit=logging.info) :
        """
        Reset the commandss positions to their original ones
        """
        for legend in legends :
            for (finger, mg, charac) in legend :
                command, command_pos = self.commands_with_positions[finger][mg][charac]
                command.set('cx', str(command_pos[0]))
                command.set('cy', str(command_pos[1]))
                    
    def duplicate_command_icons(self, mg_layer_refs, logit=logging.info) :
        """
        Duplicate the command icons to have a deported icon
        """
        for finger in mg_layer_refs.keys() :
            for mg in mg_layer_refs[finger].keys() :
                for charac in mg_layer_refs[finger][mg].keys() :
                    layer_refs = mg_layer_refs[finger][mg][charac]
                    for layer_ref in layer_refs :
                        # Check if the layer is visible to consider its command
                        layer = layer_ref.source
                        if layer.get('style') != 'display:none' :
                            # Get the command in layer_ref childrens
                            for child in layer_ref.source.getchildren() :
                                # Check if there is an attribute mgrep-path-element with value equal to COMMAND
                                if 'mgrep-path-element' in child.attrib and child.attrib['mgrep-path-element'] == u.COMMAND :    
                                    new_layer = self.svg.add(child.copy())
                                    new_layer.set("id", self.svg.get_unique_id("layer"))
                                    new_layer.style = 'display:none'
                                    new_layer.set("mgrep-path-element", u.ICON_COMMAND)
                                    # Insert to parent layer
                                    layer_ref.source.insert(0, new_layer)

    def delete_icon_commands(self, mg_layer_refs, logit=logging.info) :
        """
        Delete the icon commands
        """
        for finger in mg_layer_refs.keys() :
            for mg in mg_layer_refs[finger].keys() :
                for charac in mg_layer_refs[finger][mg].keys() :
                    layer_refs = mg_layer_refs[finger][mg][charac]
                    for layer_ref in layer_refs :
                        # Check if the layer is visible to consider its command
                        layer = layer_ref.source
                        if layer.get('style') != 'display:none' :
                            # Get the command in layer_ref childrens
                            for child in layer_ref.source.getchildren() :
                                # Check if there is an attribute mgrep-path-element with value equal to COMMAND
                                if 'mgrep-path-element' in child.attrib and child.attrib['mgrep-path-element'] == u.ICON_COMMAND :    
                                    child.delete()
        
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

    def get_legend_ref(self, nb_mgs) :
        """
        Get the legend reference corresponding to the number of mgs in the legend
        """
        match nb_mgs :
            case 1 :
                return self.legend_one_ref
            case 2 :
                return self.legend_two_ref
            case 3 :
                return self.legend_three_ref
            case 4 :
                return self.legend_four_ref
            case 5 :
                return self.legend_five_ref
            case 6 :
                return self.legend_six_ref

    def create_legend(self, legend_ref, mgs, characs, markers_with_positions, legend_type, logit=logging.info) :
        """
        Create the legend with X markers and move it to the right position
        Return the transformation matrix to the right position
        """
        # Create the legend
        legend = self.copy_legend_template(legend_ref, logit)
        # Get the position of the new legend center
        legend_center = get_legend_center(mgs, characs, markers_with_positions, logit)
        # Get the legend elements
        legend_elements = get_legend_elements(legend, len(mgs), logit)
        legend_design = legend.find(f".//*[@mgrep-legend='legend']")
        legend_elements.insert(0, legend_design)
        # Move the legend elements to the right position
        TRS_matrix = move_legend_elements(legend_elements, legend_center, legend_design, legend_type, logit)
        return TRS_matrix
        
    def move_commands_to_legend(self, legend_ref, finger, mgs, characs, legend_TRS_matrix, logit=logging.info) :
        """
        Move the microgesture commands to their corresponding legend position
        """
        # Get commands and positions
        commands, command_positions = self.get_commands_with_positions(finger, mgs, characs)
        # Get the legend's marker positions
        marker_positions = self.get_legend_marker_positions(legend_ref, len(mgs))
        # Compute the translation matrixes to move the commands to the legend
        command_TRS_matrixes = self.get_command_TRS_matrixes(command_positions, marker_positions)
        # Move the commands to the legend
        move_commands(commands, legend_TRS_matrix, command_TRS_matrixes, logit)

    def get_commands_with_positions(self, finger, mgs, characs) :
        """
        Get the commands and their positions
        """
        commands = []
        command_positions = []
        for i in range(len(mgs)) :
            command, command_pos = self.commands_with_positions[finger][mgs[i]][characs[i]]
            commands.append(command)
            command_positions.append(command_pos)
        return commands, command_positions

    def get_legend_marker_positions(self, legend_ref, nbr_mgs) :
        """
        Get the positions of the legend's markers
        """
        marker_positions = []
        for i in range(nbr_mgs) :
            marker = legend_ref.source.find(f".//*[@mgrep-legend='{get_marker_name(i)}']")
            marker_positions.append([float(marker.get('cx')), float(marker.get('cy'))])
        return marker_positions

    def get_command_TRS_matrixes(self, command_positions, marker_positions) :
        """
        Compute the translation matrixes to move the commands to the legend
        """
        TRS_matrixes = []
        for i in range(len(command_positions)) :
            TRS_matrixes.append(mg.get_translation_matrix(command_positions[i], marker_positions[i]))
        return TRS_matrixes

    def copy_legend_template(self, legend_ref, logit=logging.info) :
        """
        Create a command icon
        """
        # Copy the template
        new_legend = etree.fromstring(etree.tostring(legend_ref.source))        
        # Add to legend layer
        self.legend_layer.insert(0, new_legend)
        
        return new_legend

#####################################################################

def get_shift(legend_type) :
    """
    Get the matrix corresponding to a translation to the right
    """
    if legend_type==u.LEFT:
        return np.array([[1, 0, -45], [0, 1, -5], [0, 0, 1]])
    else :
        return np.array([[1, 0, 35], [0, 1, 5], [0, 0, 1]])

def move_legend_elements(legend_elements, middle_position, legend_design, legend_type, logit=logging.info) :
    """
    Move the legend elements to the right position
    """
    # Move the legend and the markers to the marker position
    TO_matrix = np.array([[1, 0, middle_position[0]], [0, 1, middle_position[1]], [0, 0, 1]])
    # Compute translation from the left corner of the legend_design to its centroid
    parsed_design = svg.path.parse_path(legend_design.get('d'))
    left_corner = mg.convert_from_complex(parsed_design[0].start)
    centroid = mg.get_center_path(legend_design.get('d'))
    # centroid = get_center(legend_design, logit)
    TC_matrix = mg.get_translation_matrix(centroid, left_corner)
    # Shift position from the marker
    TS_matrix = get_shift(legend_type)
    TRS_matrix = TS_matrix @ TC_matrix @ TO_matrix
    
    for legend_element in legend_elements :
        move_legend_element(legend_element, TRS_matrix, logit)
        
    return TRS_matrix

def move_legend_element(legend_element, TRS_matrix, logit=logging.info) :
    """
    Move the legend element to the right position
    """
    # If the legend element is a path
    if legend_element.tag == inkex.addNS('path', 'svg') :
        move_path(legend_element, TRS_matrix, logit)
    # If the legend element is a circle
    elif legend_element.tag == inkex.addNS('circle', 'svg') :
        move_circle(legend_element, TRS_matrix, logit)

def move_path(path_element, TRS_matrix, logit=logging.info) :
    """
    Move the path_element element to the right position
    """
    parsed_path = svg.path.parse_path(path_element.get("d"))
    parsed_path = mg.apply_matrix_to_path(parsed_path, [], TRS_matrix, logit)
    path_element.set('d', parsed_path.d())
        
def move_commands(commands, legend_TRS_matrix, TRS_matrixes, logit=logging.info) :
    """
    Move the commands to the right position
    """
    for command, TRS_matrix in zip(commands, TRS_matrixes) :
        move_circle(command, legend_TRS_matrix @ TRS_matrix, logit)

def move_circle(circle_element, TRS_matrix, logit=logging.info) :
    """
    Move the circle element to the right position
    """
    path_cx = circle_element.get("cx")
    path_cy = circle_element.get("cy")
    path_r = circle_element.get("r")
    circle = {u.COORDINATES : mg.convert_to_complex(path_cx, path_cy), u.CIRCLE_RADIUS : path_r}
    new_circle = mg.apply_matrix_to_circle(circle, [], TRS_matrix, logit)
    new_cx = new_circle[u.COORDINATES].real
    new_cy = new_circle[u.COORDINATES].imag
    circle_element.set("cx", str(new_cx))
    circle_element.set("cy", str(new_cy))
    
def get_transform_matrix(element, logit):
    """
    Get the transform matrix of an element
    """
    # Get the transform attribute
    transform = element.get('transform')
    # Get the transform matrix
    TS_matrix = np.array(inkex.transforms.Transform(transform).matrix)
    
    return TS_matrix

def set_transform_matrix(element, TS_matrix):
    """
    Set the transform matrix of an element
    """
    transform = inkex.transforms.Transform()
    matrix = [[x for x in row] for row in TS_matrix]
    transform._set_matrix(matrix)
    # Set the new transform matrix
    hexad = list(transform.to_hexad())
    new_transform = f"matrix({hexad[0]},{hexad[1]},{hexad[2]},{hexad[3]},{hexad[4]},{hexad[5]})"
    element.set('transform', new_transform)

def reset_commands(layer_ref):
    """
    Reset the commands of a layer
    """
    # Remove all elements with the attribute 'mgrep-command' set to 'template'
    for cmd in layer_ref.source.xpath(f".//*[@mgrep-command='template']") :
        cmd.getparent().remove(cmd)
        
def get_marker_and_position(mg, charac, markers_with_positions) :
    """
    Get the marker and its position
    """
    if u.RECEIVER in markers_with_positions[mg][charac] :
        return markers_with_positions[mg][charac][u.RECEIVER]
    else : 
        return markers_with_positions[mg][charac][u.TRAJ_START]

#####################################################################
    
def get_legend_center(mgs, characs, markers_with_positions, logit=logging.info) :
    """
    Get the legend center
    """
    for i in range(len(mgs)) :
        mg, charac = mgs[i], characs[i]
        if u.RECEIVER in markers_with_positions[mg][charac] :
            marker, marker_pos = markers_with_positions[mg][charac][u.RECEIVER]
        else : 
            marker, marker_pos = markers_with_positions[mg][charac][u.TRAJ_END]
        if i == 0 :
            legend_center = marker_pos
        else :
            legend_center[0] += marker_pos[0]
            legend_center[1] += marker_pos[1]
    
    legend_center[0] /= len(mgs)
    legend_center[1] /= len(mgs)
    return legend_center

def get_legend_elements(legend, nb_mgs, logit=logging.info) :
    """
    Get the legend elements
    """
    legend_elements = []
    for i in range(nb_mgs) :
        marker = legend.find(f".//*[@mgrep-legend='{get_marker_name(i)}']")
        marker.set('style', 'display:none')
        legend_elements.append(marker)
    return legend_elements

def get_marker_name(i) :
    """
    Get the marker name
    """
    match i :
        case 0 :
            return "first"
        case 1 :
            return "second"
        case 2 :
            return "third"
        case 3 :
            return "fourth"
        case 4 :
            return "fifth"
        case 5 :
            return "sixth"

#####################################################################

def _main():
    effect = AddLegend()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#####################################################################