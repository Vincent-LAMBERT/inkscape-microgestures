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
import time

import copy
import logging
import os
import tempfile
import subprocess
from inkex.elements import Group
import numpy as np
import svg.path
from lxml import etree

from microrep.map_commands.map_commands.configuration_file import *
import microrep.core.utils as u
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.export as ex

#######################################################################################################################

class MapCommands(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpeg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument("--showMg", type=inkex.Boolean, dest="showMg", default=False, help="Show microgesture type")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export")
        self.arg_parser.add_argument("--icon", type=str, dest="icon", default="~/", help="Icon folder")
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
        
        self.start_time = time.time()
    
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
        
        self.compute_visible_points(logit)
        
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = rf.get_layer_refs(self.document, False, logit)
        self.mg_layer_refs = rf.get_mg_layer_refs(layer_refs, logit)
        
        # Get a dictionnary of the wanted mappings with their characteristics
        mappings = get_mappings(self.options.config, logit)
        # Get all commands in mappings
        command_names = get_command_names(mappings, logit)
        # Add the command icons to the svg
        dirname = os.path.dirname(__file__)
        document = etree.parse(f"{dirname}/Icon/Icon.svg")
        self.command_template_ref = rf.get_layer_refs(document, False, logit)[0]
        self.icon_SVG_refs = self.get_icon_SVGs_refs(self.options.icon, command_names, logit)
        
        # Create the mapping layer
        self.mapping_layer = self.create_mapping_layer()
        
        for mapping in mappings :
            self.change_mapping(mapping, logit)            
            # Actually do the export into the destination path.
            family_name = self.svg_name.split("_")[0]
            logit(f"Exporting {family_name}_{get_mapping_name(mapping)}")
            ex.export(self.document, f"{family_name}_{get_mapping_name(mapping)}", self.options, logit)
            self.reset_mapping()
            
        # Delete layer with label "Mappings"
        self.mapping_layer.delete()    

#####################################################################
    
    def create_mapping_layer(self) :
        """
        Creates the layer that will handle all the commands
        It is placed above all the existing layers to be visible
        """
        mapping_layer = Group.new('Mappings', is_layer=True)
        # Add mapping layer to the document
        self.document.getroot().append(mapping_layer)
        # self.mapping_layer.insert(0, mapping_layer)
        return mapping_layer
        
    def change_mapping(self, mapping, logit=logging.info) :
        """
        Change the mapping of the svg according to the mapping dictionnary
        and the command icons
        """
        for fmc, command in mapping :
            finger, mg, charac = fmc
            for layer_ref in self.mg_layer_refs[finger][mg][charac] :
                # Check if the layer and all its parents are visible
                if not layer_ref.is_visible() :
                    continue
                command_icon = self.create_command(command, logit, text=True)
                if (self.options.showMg) :
                    # Add the microgesture in the command texts
                    text = f"[{mg}]"
                    add_text_to_command(text, command_icon, logit)
                self.adapt_command_to_layer(layer_ref, command_icon, logit)
                if has_duplicated_command_icon(layer_ref) :
                    duplicated_command_icon = self.create_command(command, logit, text=False)
                    self.adapt_icon_command_to_layer(layer_ref, duplicated_command_icon, logit)

    def adapt_command_to_layer(self, layer_ref, new_command, logit=logging.info) :
        """
        Add a command to a layer
        """
        # Find child of layer with 'mgrep-path-element' with 
        # the value of 'command'
        command = layer_ref.source.find(f".//*[@mgrep-path-element='{u.COMMAND}']")

        text_marker_pairs = get_text_marker_pairs(new_command, logit)
        
        if command is not None :
            # Insert the new command above all existing commands and at the placeholded location
            command_layer = self.adapt_command_to_placeholder(command, new_command, logit)
            self.mapping_layer.insert(0, command_layer)
            
            # Show the text that crosses the less of other designs
            self.hide_text(text_marker_pairs, command, logit)
                
        # The text origin and transform matrix is 
        # overwritten by the insertion. 
        # Thus we have to use markers and move each 
        # text to the corresponding location after 
        # the template insertion
        for text, marker in text_marker_pairs :
            self.move_text_to_marker(text, marker, logit)

    def move_text_to_marker(self, text, marker, logit):
        """
        Move a text to a marker position
        """
        #Adjust the transform matrix
        marker_position = np.array([float(marker.get('cx')), float(marker.get('cy'))])
        # Get the transform matrix of the text
        TS_matrix = get_transform_matrix(text, logit)
        # Change the translation part of the matrix
        # to match the marker position
        TS_matrix[:,2] = marker_position
        # Set the new transform matrix
        set_transform_matrix(text, TS_matrix)
        
        # Adjust the anchor
        # Get the textspan which is the child of the text
        textspan = text.find('svg:tspan', namespaces=inkex.NSS)
        # Adjust the text-align style
        text_style = textspan.get('style')
        text_type =  text.attrib['mgrep-command'].split(",")[1].replace(" ", "")
        new_style = f"text-align:{u.TEXT_ALIGNS[text_type]};text-anchor:{u.TEXT_ANCHORS[text_type]}"
        textspan.set('style', new_style)         

    def hide_text(self, text_marker_pairs, cmd, logit=logging.info) :
        """
        Hides the text that may hide other elements
        """
        # Get all the existing markers
        markers = self.get_markers(logit)
        # Get all the visible points
        points = self.visible_points
        
        # Get the current point
        cmd_position = np.array([float(cmd.get('cx')), float(cmd.get('cy'))])
        # Check if their exist a marker not too far from the command which is 
        # not the one that has been used to place the command, hence the minimum distance
        ISSUE_DISTANCE = 35
        SECURITY_DISTANCE = 7
        
        # If one marker is too close to the command define the direction in which it is preferable to show the text
        close_markers = get_close_markers(cmd_position, markers, SECURITY_DISTANCE, ISSUE_DISTANCE, logit)
        

        if len(close_markers) > 0 :
            # Check if the close markers have the attribute mgrep-legend
            if is_close_to_legend(close_markers) :
                show_specific_text(text_marker_pairs, u.RIGHT, logit)
            else :
                close_points = get_close_points(cmd_position, points, SECURITY_DISTANCE, ISSUE_DISTANCE, logit)
                text_zone = self.compute_text_zone(text_marker_pairs, cmd_position, close_points, logit)
                    
                show_specific_text(text_marker_pairs, text_zone, logit)
        else :
            show_specific_text(text_marker_pairs, u.BELOW, logit)
            
    def compute_text_zone(self, text_marker_pairs, cmd_position, close_points, logit=logging.info) :
        """
        Compute the text zones
        """
        text_zones = {u.BELOW:0, u.LEFT:0, u.RIGHT:0, u.ABOVE:0}
        text_zone = get_text_zone(text_zones, cmd_position, close_points, logit)
        
        # Get all the active markers
        active_markers = self.get_active_markers_positions(logit)
        
        while text_collision(active_markers, text_marker_pairs, text_zone, 5, logit) and len(text_zones) > 1:
            text_zones.pop(text_zone)
            text_zone = get_text_zone(text_zones, cmd_position, close_points, logit)
        
        # Get all the icons positions
        icons = self.get_icon_positions(logit)
        
        while text_collision(icons, text_marker_pairs, text_zone, 10, logit) and len(text_zones) > 1:
            text_zones.pop(text_zone)
            text_zone = get_text_zone(text_zones, cmd_position, close_points, logit)

        return text_zone
                
    def adapt_icon_command_to_layer(self, layer_ref, new_command, logit):
        """
        Move the icon command to the layer
        """
        # Find child of layer with 'mgrep-path-element' with 
        # the value of 'icon-command'
        command = layer_ref.source.find(f".//*[@mgrep-path-element='{u.ICON_COMMAND}']")
        
        if command is not None :
            # Insert the new command above all existing commands and at the placeholded location
            command_layer = self.adapt_command_to_placeholder(command, new_command, logit)
            self.mapping_layer.insert(0, command_layer)

    def adapt_command_to_placeholder(self, command_placeholder, new_command, logit):
        """
        Move the command to the placeholder
        """
        # Get the centroid of the placeholder in the document
        placeholder_centroid = np.array([float(command_placeholder.get('cx')), float(command_placeholder.get('cy'))])
        placeholder_radius = float(command_placeholder.get('r'))
        
        # Get the centroid of the command icon template
        command = new_command.find(".//*[@mgrep-icon='template']")
        command_centroid = np.array([float(command.get('cx')), float(command.get('cy'))])
        command_radius = float(command.get('r'))
        
        origin = np.array([0,0])
        
        # Get translation to apply to the command icon to match the centroid of the placeholder        
        T_origin_matrix = mg.get_translation_matrix(command_centroid, origin)    
        T_placeholder_matrix = mg.get_translation_matrix(origin, placeholder_centroid)
        # Get scaling to apply to the command icon to match the size of the placeholder
        factor = placeholder_radius / command_radius
        S_matrix = mg.get_scaling_matrix_from_factor(factor)
        
        for xml in new_command.findall(".//{*}path") :
            parsed_path = svg.path.parse_path(xml.get("d"))
            TRS_matrix = T_placeholder_matrix @ S_matrix @ T_origin_matrix
            parsed_path = mg.apply_matrix_to_path(parsed_path, [], TRS_matrix, logit)
            xml.set('d', parsed_path.d())
        for xml in new_command.findall(".//{*}circle") :
            path_cx = xml.get("cx")
            path_cy = xml.get("cy")
            path_r = xml.get("r")
            circle_coords = {u.COORDINATES : mg.convert_to_complex(path_cx, path_cy), u.CIRCLE_RADIUS : path_r}
            
            # Tests wheter it is a design or command circle we may have to scale 
            # or a marker that should be translated by the scaling factor
            # It is indicated by the mgrep-command
            mgrep_command = xml.get("mgrep-command")
            if mgrep_command != None and mgrep_command.split(", ")[0] == "marker" :
                TRS_matrix = T_placeholder_matrix @ S_matrix @ T_origin_matrix
                # Adjust if the element is the below text
                if xml.get("mgrep-command")=="marker, below":
                    T_marker = mg.get_translation_matrix(np.array([0, -2]), np.array([0, 0]))
                    TRS_matrix = T_marker @ TRS_matrix 
            else :
                TRS_matrix = T_placeholder_matrix @ T_origin_matrix
                    
            circle = mg.apply_matrix_to_circle(circle_coords, [], TRS_matrix, logit)
            xml.set("cx", str(circle[u.COORDINATES].real))
            xml.set("cy", str(circle[u.COORDINATES].imag))
            xml.set("r", str(float(circle[u.CIRCLE_RADIUS])*factor))
            
        return new_command
                
    def reset_mapping(self) :
        """
        Reset the mapping of the svg
        """
        # Empty the mapping_layer
        self.mapping_layer.clear()

    def create_command(self, command, logit, text=True) :
        """
        Create a command icon with maybe text
        """
        # Copy the template
        new_command_document = etree.fromstring(etree.tostring(self.command_template_ref.source))
        # Get the centroid of the command icon template
        template = new_command_document.xpath('//svg:circle[@mgrep-icon="template"]', namespaces=inkex.NSS)[0]
        
        if text :
            # Replace the command texts by the command name
            for text in new_command_document.xpath('//svg:text', namespaces=inkex.NSS) :
                textspan = text.xpath('.//svg:tspan', namespaces=inkex.NSS)[0]
                # Set command name with capitalized first letter
                textspan.text = command.capitalize()
                
            # Hide the markers
            marker_left = new_command_document.find('.//svg:circle[@mgrep-command="marker, left"]', namespaces=inkex.NSS)
            marker_right = new_command_document.find('.//svg:circle[@mgrep-command="marker, right"]', namespaces=inkex.NSS)
            marker_below = new_command_document.find('.//svg:circle[@mgrep-command="marker, below"]', namespaces=inkex.NSS)
            marker_above = new_command_document.find('.//svg:circle[@mgrep-command="marker, above"]', namespaces=inkex.NSS)
            marker_left.set("style", "display:none")
            marker_right.set("style", "display:none")
            marker_below.set("style", "display:none")
            marker_above.set("style", "display:none")
        else :
            # Delete the layer with the label "Text" in the template
            text_layer = new_command_document.find('.//svg:g[@inkscape:label="Text"]', namespaces=inkex.NSS)
            text_layer.getparent().remove(text_layer)
        
        # Get all layers of the command icon
        icon = etree.fromstring(etree.tostring(self.icon_SVG_refs[command].source))
        # Get the centroid of the command icon
        icon_centroid = icon.xpath('//svg:circle[@mgrep-icon="centroid"]', namespaces=inkex.NSS)[0]
        
        # Get xml of the layer with the attribute 'mgrep-icon' = 'command'
        icon_xml = icon.xpath('//svg:g[@mgrep-icon="command"]', namespaces=inkex.NSS)[0]
        
        # Get translation to apply to the command icon to match the centroid of the command icon template
        template_point = np.array([float(template.get('cx')), float(template.get('cy'))])
        icon_centroid_point = np.array([float(icon_centroid.get('cx')), float(icon_centroid.get('cy'))])
        
        T_matrix = mg.get_translation_matrix(icon_centroid_point, template_point)
        
        for xml in icon_xml.findall(".//{*}path") :
            parsed_path = svg.path.parse_path(xml.get("d"))
            parsed_path = mg.apply_matrix_to_path(parsed_path, [], T_matrix, logit)
            xml.set('d', parsed_path.d())
        for xml in icon_xml.findall(".//{*}circle") :
            path_cx = xml.get("cx")
            path_cy = xml.get("cy")
            circle = mg.compute_point_transformation(mg.convert_to_complex(path_cx, path_cy), [], T_matrix, logit)
            xml.set("cx", str(circle.real))
            xml.set("cy", str(circle.imag))
            
        # Add child to the parent of the template layer
        # The +1 is to insert the icon above the template
        #element to make our icon visible
        parent = template.getparent()
        parent.insert(parent.index(template)+1, icon_xml)
        
        # Get the layer with the attribute 'mgrep-command' = 'template'
        # to be inserted in the svg
        new_command = new_command_document.xpath('//svg:g[@mgrep-command="template"]', namespaces=inkex.NSS)[0]
        
        return new_command

    def get_icon_SVGs_refs(self, icon_folder_path, command_names, logit):
        """
        Returns the command icon SVG template and the command icons
        """
        # Get the command icon SVG template
        commands = dict()
        
        for command in command_names :
            document = etree.parse(f"{icon_folder_path}{command}.svg")
            icon_SVG = rf.get_layer_refs(document, False, logit)[0]
            commands[command] = icon_SVG
            
        return commands

#####################################################################
    
    def compute_visible_points(self, logit=logging.info) -> list :
        """
        Get all the points of the representations
        Those points are the points of the path of the representation that are visible
        and located under the Designs layer. They have the attribute 'mgrep-path-element' = design
        """
        # Get the Designs layer
        designs_layer = self.document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)
        # Get the visible layers that are child of the Designs layer
        visible_layers = [child for child in designs_layer[0].getchildren() if child.get("style") != "display:none"]
        # Get the design path for each visible layer
        design_points = []
        for layer in visible_layers :
            for child in layer.getchildren() :
                if child.get("mgrep-path-element") == "design" :
                    # Get all points of the path
                    path = svg.path.parse_path(child.get("d"))
                    path_points = [mg.convert_from_complex(path.point(i)) for i in np.linspace(0, 1, 20)]
                    design_points += path_points
        self.visible_points = design_points
                    
    def get_markers(self, logit) -> list :
        """
        Get all positions of the elements having the attribute 'mgrep-marker'
        """
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        
        #Get the layers having the attribute 'mgrep-marker'
        markers = []
        for layer in svg_layers :
            if layer.get('mgrep-marker') :
                # Get the marker in the layer 
                marker = layer.xpath('.//svg:circle', namespaces=inkex.NSS)[0]
                markers.append(marker)
            else :
                for child in layer.getchildren() :
                    if (child.get('mgrep-legend') and child.get('mgrep-legend') != 'legend') :
                        # Get the potential legend markers with the attribute 'mgrep-legend' whose
                        # value is not 'legend'
                        markers.append(child)    
        
        return markers

    def get_active_markers_positions(self, logit) -> list :
        """
        Get all the text_box positions in the SVG
        """
        svg_circles = self.document.xpath('//svg:circle', namespaces=inkex.NSS)
        
        # Get only the active markers
        active_markers = []
        for circle in svg_circles :
            if circle.get('mgrep-status')=='active' :
                position = np.array([float(circle.get('cx')), float(circle.get('cy'))])
                active_markers.append(position)
        
        return active_markers

    def get_icon_positions(self, logit) -> list :
        """
        Get all the icon positions in the SVG
        """
        # Get Designs layer
        designs_layer = self.document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)
        
        # Get circles in the Designs layer
        svg_circles = designs_layer[0].xpath('.//svg:circle', namespaces=inkex.NSS)
        
        icons = []
        for circle in svg_circles :
            if circle.get('mgrep-path-element')==u.COMMAND:
                position = np.array([float(circle.get('cx')), float(circle.get('cy'))])
                icons.append(position)
        
        return icons

#####################################################################

def get_command_names(mappings, logit):
    """
    Get all commands in mappings
    Each mapping has the form 
    """
    command_names = list()
    for mapping in mappings :
        for command in get_mapping_commands(mapping, logit=logging.info) :
            if command not in command_names :
                command_names.append(command)
    return command_names
    
def get_text_marker_pairs(command, logit):
    """
    Get a list of text and marker pairs
    """
    text_marker_pairs = list()
    for text in command.xpath(".//svg:text", namespaces=inkex.NSS) :
        if 'mgrep-command' in text.attrib :
            text_type =  text.attrib['mgrep-command'].split(",")[1]
            text_type = text_type.replace(" ", "")
            for marker in command.xpath(".//svg:circle", namespaces=inkex.NSS) :
                if 'mgrep-command' in marker.attrib :
                    marker_type =  marker.attrib['mgrep-command'].split(",")[1]
                    marker_type = marker_type.replace(" ", "")
                    if text_type == marker_type :
                        text_marker_pairs.append((text, marker))
    return text_marker_pairs

        
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
        
def compute_new_style(original_style, style_combination, logit=logging.info) :
    """
    Compute the new style of the element
    """
    new_style = ""
    for style in original_style.split(";") :
        if style != "" :
            key, value = style.split(":")
            if key in style_combination and value!='none' and value!='None':
                new_style += f"{key}:{style_combination[key]};"
            else :
                new_style += f"{key}:{value};"
    return new_style

def show_specific_text(text_marker_pairs, text_position, logit=logging.info) :
    """
    Show the text corresponding to the given position
    and hide the others
    """    
    for text, marker in text_marker_pairs :
        marker_type = marker.get("mgrep-command").split(",")[1]
        marker_type = marker_type.replace(" ", "")
        if marker_type == text_position :
            new_style_element = {"display":"inline"}
            marker.set("mgrep-status", "active")
        else :
            new_style_element = {"display":"none"}
            marker.set("mgrep-status", "inactive")
        original_style = text.get("style")
        new_style = compute_new_style(original_style, new_style_element, logit)
        text.set("style", new_style)

def get_close_markers(origin, markers, min_distance, max_distance, logit=logging.info) :
    """
    Get the markers that are close to the origin
    """
    close_markers = []
    for marker in markers :
        marker_position = np.array([float(marker.get('cx')), float(marker.get('cy'))])
        distance = int(np.linalg.norm(marker_position - origin))
        if min_distance <= distance <= max_distance :
            close_markers.append(marker)
    return close_markers

def get_close_points(origin, points, min_distance, max_distance, logit=logging.info) :
    """
    Get the points that are close to the origin
    """
    close_points = []
    for point in points :
        distance = int(np.linalg.norm(point - origin))
        if min_distance <= distance <= max_distance :
            close_points.append(point)
    # Filter the points to keep fuse the points that are close to each other
    fused_close_points = []
    while len(close_points) > 0 :
        point_i = close_points.pop()
        # If there are close points in close_points, remove them
        close_points = [point for point in close_points if np.linalg.norm(point_i - point) > min_distance]
        fused_close_points.append(point_i)
        
    return fused_close_points

def text_collision(points, text_marker_pairs, text_position, height, logit=logging.info) :
    """
    Check if there is a collision between the future text and the existing text boxes
    """
    # Consider that the future text box would be at the text_position and would have a width of 50
    # Compute the bounding box of the future text
    
    for text, marker in text_marker_pairs :
        marker_type = marker.get("mgrep-command").split(",")[1]
        marker_type = marker_type.replace(" ", "")
        if marker_type == text_position :
            future_bbox = compute_bbox(marker, text_position, height, logit)
    
    for point_pos in points :
        if point_in_bbox(point_pos, future_bbox) :
            return True
    return False

def compute_bbox(text_marker, text_direction, height, logit=logging.info) :
    """
    Compute the bounding box of the text
    """
    marker_pos = np.array([float(text_marker.get('cx')), float(text_marker.get('cy'))])
            
    # width = 25
    width = 50
    
    if text_direction==u.LEFT :
        top_left = marker_pos + np.array([-width, -height/2])
        bottom_right = marker_pos + np.array([0, height/2])
    elif text_direction==u.RIGHT :
        top_left = marker_pos + np.array([0, -height/2])
        bottom_right = marker_pos + np.array([width, height/2])
    else :
        top_left = marker_pos + np.array([-width/2, -height/2])
        bottom_right = marker_pos + np.array([width/2, height/2])
    
    return [top_left, bottom_right]
    
def point_in_bbox(point_pos, bbox) :
    """
    Check if the marker is in the bounding box
    """
    if bbox[0][0] <= point_pos[0] <= bbox[1][0] and bbox[0][1] <= point_pos[1] <= bbox[1][1] :
        return True
    return False

def get_text_zone(text_zones, command_origin, close_points, logit=logging.info) :
    """
    Get the text zone according to the position of the points
    """
    for point in close_points :
        # Determine the directions of the point
        dir_values = get_directions(text_zones, command_origin, point, logit)
        for dir, value in dir_values :
            text_zones[dir] += value
    # Get direction(s) with the minimum number of points
    min_dirs = get_min_directions(text_zones, logit)
    if len(min_dirs) > 1 :
        # If there is more than one direction, choose the one that is the opposite of the direction
        # with the maximum number of points
        max_dir = max(text_zones, key=text_zones.get)
        return get_opposite_min_direction(min_dirs, max_dir, logit)
    return min_dirs[0]

def get_min_directions(text_zones, logit=logging.info) :
    """
    Get the direction(s) with the minimum number of points
    """
    min_dirs = []
    min_value = min(text_zones.values())
    for dir, value in text_zones.items() :
        if value == min_value :
            min_dirs.append(dir)
    return min_dirs

def get_opposite_min_direction(min_dirs, max_dir, logit=logging.info) :
    """
    Get the direction that is the opposite of the direction max_dir
    """
    if u.OPPOSITE_ANCHORS[max_dir] in min_dirs :
        return u.OPPOSITE_ANCHORS[max_dir]
    else :
        return min_dirs[0]

def get_directions(text_zones, command_origin, point_pos, logit=logging.info) :
    """
    Get the direction of the point_pos according to the command_origin
    """
    SECURITY_DISTANCE = 7
    dirs = []
    vector = point_pos - command_origin
    for dir in text_zones.keys() :
        if is_in_direction(dir, vector, logit=logging.info) :
            distance = round(1/(np.linalg.norm(vector)-SECURITY_DISTANCE), 5)
            dirs.append([dir, distance])
    return dirs
    
def is_in_direction(dir, vector, logit=logging.info) :
    """
    Check if the vector is in the direction dir according to the DIRECTIONS_VECTORS_ASSOCIATIONS
    """
    norm_vector = vector/np.linalg.norm(vector)
    if dir == u.ABOVE and norm_vector[1] < 0 and -0.87 < norm_vector[0] < 0.87:
        return True
    elif dir == u.BELOW and norm_vector[1] > 0 and -0.87 < norm_vector[0] < 0.87:
        return True
    elif dir == u.LEFT and norm_vector[0] < 0 and -0.5 < norm_vector[1] < 0.5 :
        return True
    elif dir == u.RIGHT and norm_vector[0] > 0 and -0.5 < norm_vector[1] < 0.5  :
        return True
    else :
        return False
        
def has_duplicated_command_icon(layer_ref) :
    """
    Check if the layer has an icon-command
    """
    return layer_ref.source.find(f".//*[@mgrep-path-element='{u.ICON_COMMAND}']") is not None

def is_close_to_legend(close_points) :
    """
    Check if the point is close to a legend
    """
    close_points_with_legend = []
    for point in close_points :
        if point.get("mgrep-legend") is not None :
            close_points_with_legend.append(point)

    return len(close_points_with_legend) > 0

def add_text_to_command(mg_text, cmd, logit=logging.info) :
    """
    Add the text to the command
    """
    # Replace the command texts by the command name
    for text in cmd.xpath('//svg:text', namespaces=inkex.NSS) :
        textspan = text.xpath('.//svg:tspan', namespaces=inkex.NSS)[0]
        # Set command name with capitalized first letter
        original_text = textspan.text
        textspan.text = f"{mg_text.upper()} {original_text}"
        
#####################################################################

#####################################################################

def _main():
    effect = MapCommands()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#######################################################################################################################