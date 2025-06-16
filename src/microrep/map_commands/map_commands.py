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
import copy
import json
import logging
import os
import subprocess
import tempfile
import time
from importlib.resources import files

import inkex
import numpy as np
import svg.path
from inkex.elements import Group, PathElement, TextElement, Tspan
from inkex.paths import Path
from lxml import etree

import microrep.core.export as ex
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.utils as u
from microrep.map_commands.configuration_file import *

#######################################################################################################################

class MapCommands(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument("--showMg", type=inkex.Boolean, dest="showMg", default=False, help="Show microgesture type")
        self.arg_parser.add_argument("--radius", type=float, dest="radius", default=u.BASE_RADIUS, help="Command radius")
        self.arg_parser.add_argument("--prefix", type=str, dest="prefix", default='', help="Export Prefix")
        self.arg_parser.add_argument("--name", type=str, dest="name", default='', help="Export Name (overrides the prefix if set)")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export")
        self.arg_parser.add_argument("--icons", type=str, dest="icons", default="~/", help="Icons folder")
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
        
        # Get a dictionnary of the wanted mappings with their characteristics
        mappings = get_mappings(self.options.config, logit)
        # Get all commands in mappings
        command_names = get_command_names(mappings, logit)
        # Add the command icons to the svg
        document = etree.parse(str(files('microrep').joinpath('map_commands/icon_placeholder.svg')))
        self.command_template_ref = rf.get_layer_refs(document, False, logit)[0]
        self.icon_SVG_refs = self.get_icon_SVGs_refs(self.options.icons, command_names, logit)
        
        # Check if there is an element with the attribute 'mgrep-legend' somewhere
        if self.document.xpath('.//*[@mgrep-legend]') :
            legend_exist = True
            visible_designs, visible_hands = None, None
        else :
            legend_exist = False
            visible_designs, visible_hands = self.compute_visible_designs(self.document, logit)
        
        for mapping in mappings :
            # Sets the radius of the commands
            new_document = ex.special_deepcopy(self.document)
        
            # Create the mapping layer
            mapping_layer = self.create_mapping_layer(new_document)
            
            # self.compute_visible_points(new_document, logit)            
            self.set_commands_radius(new_document, mapping, self.options.radius, logit)

            self.change_mapping(new_document, mapping_layer, mapping, legend_exist, visible_designs, visible_hands, logit)   
            
            # Actually do the export into the destination path.
            if self.options.name=='' :
                family_name = self.svg_name.split("_")[0]
                name = f"{family_name}_{get_mapping_name(mapping)}"
            else :
                name = self.options.name
                self.options.prefix = '' # to make sure it is overidden
                
            logit(f"Exporting {name}")
            ex.export(new_document, name, self.options, logit)

#####################################################################
    
    def create_mapping_layer(self, document) :
        """
        Creates the layer that will handle all the commands
        It is placed above all the existing layers to be visible
        """
        mapping_layer = Group.new('Mappings', is_layer=True)
        # Add mapping layer to the document
        document.getroot().append(mapping_layer)
        return mapping_layer
        
    def change_mapping(self, document, mapping_layer, mapping, legend_exist, visible_designs, visible_hands, logit=logging.info) :
        """
        Change the mapping of the svg according to the mapping dictionnary
        and the command icons
        """
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = rf.get_layer_refs(document, False, logit)
        mg_layer_refs = rf.get_mg_layer_refs(layer_refs, logit)
        
        command_dicts = {}
        for fmc, command_name in mapping :
            finger, mg, charac = fmc
            command_name = command_name.capitalize()
            
            command_icon = self.create_command(command_name, logit, text=True)
            if (self.options.showMg) :
                # Add the microgesture in the command texts
                text = f"[{mg}]"
                add_text_to_command(text, command_icon, logit)
                    
            for layer_ref in mg_layer_refs[finger][mg][charac] :
                # Check if the layer and all its parents are visible
                if not layer_ref.is_visible() : continue
                self.adapt_command_to_layer(mapping_layer, layer_ref, command_icon, command_dicts, command_name, logit)

        self.hide_obstructing_labels(command_dicts, legend_exist, visible_designs, visible_hands, logit)

    def adapt_command_to_layer(self, mapping_layer, layer_ref, new_command, command_dicts, command_name, logit=logging.info) :
        """
        Add a command to a layer
        """        
        if has_main_command_icon(layer_ref) :
            # Insert the new command above all existing commands and at the placeholded location
            command_circle = layer_ref.source.find(f".//*[@{u.MREP_PATH_ELEMENT}='{u.COMMAND}']")
            command_layer = self.adapt_command_to_placeholder(command_circle, new_command, logit)
            mapping_layer.insert(0, command_layer)
            command_dicts[command_name] = self.fill_command_dicts(command_circle, new_command, 0, logit)
    
        if has_duplicated_command_icon(layer_ref) :
            duplicated_command_icon = self.create_command(command_name, logit, text=False)
            self.adapt_icon_command_to_layer(layer_ref, mapping_layer, duplicated_command_icon, logit)
            
    def fill_command_dicts(self, command_circle, new_command, shift, logit=logging.info) :
        """
        Fill the command dictionnary with empty values
        """
        text_marker_pairs = get_text_marker_pairs(new_command, shift, logit)
            
        # The text origin and transform matrix is 
        # overwritten by the insertion. 
        # Thus we have to use markers and move each 
        # text to the corresponding location after 
        # the template insertion
        text_boxes = {}
        background_text_boxes = {}
        for text_type in text_marker_pairs.keys() :
            for marker in text_marker_pairs[text_type].keys() :
                texts = text_marker_pairs[text_type][marker]
                for text in texts:
                    text_box = self.move_text_to_marker(text_type, text, marker, logit)
                    if text_boxes.get(text_type)==None :
                        text_boxes[text_type] = text_box
                    else :
                        background_text_boxes[text_type] = text_box
            
        return {"icon": command_circle, "text_boxes": text_boxes, "background_text_boxes": background_text_boxes, "command_xml": new_command}

    def move_text_to_marker(self, text_type, text, marker, logit=logging.info) :
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
        if textspan != None:
            new_style = f"text-align:{u.TEXT_ALIGNS[text_type]};text-anchor:{u.TEXT_ANCHORS[text_type]}"
            textspan.set('style', new_style)
        
        text_box = compute_text_box(text, marker, text_type, logit)
        return {"xml": text, "box": text_box}
    
    def hide_obstructing_labels(self, command_dicts, legend_exist, visible_designs, visible_hands, logit=logging.info) :
        """
        Hide the labels that may obstruct the commands
        """
        obstructions = {}
        for command_name in command_dicts.keys() :
            # Show the text that crosses the less of other designs
            obstructions[command_name] = self.compute_obstructions_with_commands(command_name, command_dicts, legend_exist, logit)
        
        # Order the commands in a list according to the number of obstructions
        # The command with the most obstructions will be the first
        ordered_commands = sorted(obstructions, key=lambda x: sum([1 for key in obstructions[x].keys() if obstructions[x][key]]), reverse=True)
        
        # IT IS MANDATORY TO FIRST COMPUTE THE OBSTRUCTIONS 
        # AND THEN HIDE THE TEXTS BECAUSE THERE IS INTERDEPENDENCIES
        
        # We hide the texts that obstruct other commands
        for command_name in ordered_commands :
            self.hide_text_obstructing_commands(obstructions, command_dicts, command_name, logit)
        
        definitive_texts = {command_name: None for command_name in ordered_commands}
        
        for command_name in ordered_commands :
            obstructions, definitive_texts = self.hide_text_obstructing_designs(command_name, command_dicts, obstructions, definitive_texts, logit)
                    
        for command_name in obstructions.keys() :
            for direction in obstructions[command_name].keys() :
                obstructions[command_name][direction] = {u.COLLIDE_WITH_DESIGNS: 100, 
                                                         u.COLLIDE_WITH_HAND: 100}
                collision_with_designs = self.compute_collision_with_paths(command_dicts[command_name]["text_boxes"][direction]["box"], visible_designs, logit)
                collision_with_hand = self.compute_collision_with_paths(command_dicts[command_name]["text_boxes"][direction]["box"], visible_hands, logit)
                obstructions[command_name][direction][u.COLLIDE_WITH_DESIGNS] = collision_with_designs
                obstructions[command_name][direction][u.COLLIDE_WITH_HAND] = collision_with_hand*2
                
            obstructions, definitive_texts = self.hide_text_obstructing_definite_text(command_name, command_dicts, obstructions, definitive_texts, logit)            
                            
    def compute_obstructions_with_commands(self, command_name, command_dicts, legend_exist, logit=logging.info) :
        """
        Compute the texts that may obstruct other commands
        """        
        if legend_exist :
            obstructions = {u.RIGHT: False}
        else :
            obstructions = {u.BELOW: False, u.LEFT: False, u.RIGHT: False, u.ABOVE: False}
            
            for direction in obstructions.keys() :
                collision_with_commands = self.compute_collision_with_commands(command_dicts, direction, command_name, logit)
                obstructions[direction] = collision_with_commands
                
            # Check if there is all the directions are obstructed 
            shift = 0.1
            while all(obstructions.values()) :
                command_circle = command_dicts[command_name]["icon"]
                new_command = command_dicts[command_name]["command_xml"]
                # self.fill_command_dicts(command_circle, new_command, shift, logit)
                command_dicts[command_name] = self.fill_command_dicts(command_circle, new_command, shift, logit)
                
                for direction in obstructions.keys() :
                    collision_with_commands = self.compute_collision_with_commands(command_dicts, direction, command_name, logit)
                    obstructions[direction] = collision_with_commands
        
        return obstructions
    
    def compute_obstructions_with_definitive_texts_for_cmd_obstruction(self, obstructions, command_dicts, command_name, definitive_texts, logit=logging.info) :
        """
        Compute the texts that may obstruct the icon of other commands
        """        
        for direction in obstructions[command_name].keys() :
            # We check if there is an obstruction with definitive texts only 
            if obstructions[command_name][direction] != True:
                dir_text_box = command_dicts[command_name]["text_boxes"][direction]["box"]
                obstructions[command_name][direction] = self.compute_obstruction_with_definitive_texts(dir_text_box, definitive_texts, logit)
        return obstructions[command_name]
    
    def compute_obstructions_with_definitive_texts_for_text_obstruction(self, obstructions, command_dicts, command_name, definitive_texts, logit=logging.info) :
        """
        Compute the texts that may obstruct the text of other commands
        """        
        for direction in obstructions[command_name].keys() :
            # We check if there is an obstruction with definitive texts only 
            dir_text_box = command_dicts[command_name]["text_boxes"][direction]["box"]
            if self.compute_obstruction_with_definitive_texts(dir_text_box, definitive_texts, logit):
                obstructions[command_name][direction] = True
        return obstructions[command_name]
                
    def compute_obstruction_with_definitive_texts(self, dir_text_box, definitive_texts, logit=logging.info):
        """
        Compute the texts that may obstruct the definitive text of other commands
        """        
        for command in definitive_texts.keys():
            text_box = definitive_texts[command]
            if text_box != None :
                obstruction = self.collide(dir_text_box, text_box, logit)
                if obstruction :
                    return True
        return False
                
    def compute_definitive_texts_for_cmd_obstruction(self, obstructions, command_dicts, command_name, logit=logging.info) :
        """
        Compute the definitive text knowing the possible obstructions with other command icons
        """        
        directions_with_no_obstruction = [direction for direction in obstructions[command_name].keys() if not obstructions[command_name][direction]]    
        
        # Check if there is one and only one direction with no obstruction
        if len(directions_with_no_obstruction) == 1 :
            direction = directions_with_no_obstruction[0]
            return command_dicts[command_name]["text_boxes"][direction]["box"], direction
        else :
            return None, None
    
    def compute_definitive_texts_for_text_obstruction(self, obstructions, command_dicts, command_name, logit=logging.info):
        """
        Compute the definitive text knowing the possible obstructions with other command texts
        """        
        directions_with_no_obstruction = [direction for direction in obstructions[command_name].keys() if obstructions[command_name][direction]!=True] # Don't use 'not' because we want to push out 'True' but not dictionaries
        
        if len(directions_with_no_obstruction) > 0 :
            # Get the directions with the less collision with designs
            min_collision = min([obstructions[command_name][direction][u.COLLIDE_WITH_DESIGNS]+obstructions[command_name][direction][u.COLLIDE_WITH_HAND] for direction in directions_with_no_obstruction])
            
            directions_with_min_collision = [direction for direction in directions_with_no_obstruction if obstructions[command_name][direction][u.COLLIDE_WITH_DESIGNS]+obstructions[command_name][direction][u.COLLIDE_WITH_HAND] == min_collision]
            # If there is one and only one direction with the less collision with designs, hide the others
            chosen_direction = directions_with_min_collision[0]
            # self.hide_other_texts(chosen_direction, command_dicts, command_name, logit)
            return command_dicts[command_name]["text_boxes"][chosen_direction]["box"], chosen_direction
        else :
            return None, None
    
    # def hide_obstructing_text_pairs(self, obstructions, command_dicts, command_name, logit): 
    def hide_text_obstructing_commands(self, obstructions, command_dicts, command_name, logit=logging.info) :
        """
        Hide the texts that may obstruct other commands
        """
        # Get the directions with no collision with commands
        collision_with_commands = [direction for direction in obstructions[command_name].keys() if obstructions[command_name][direction]]
        
        for direction in collision_with_commands:
            self.hide_text(command_dicts, command_name, direction)
        return collision_with_commands
    
    def hide_text_obstructing_designs(self, command_name, command_dicts, obstructions, definitive_texts, logit=logging.info) :
        """
        Hide the texts that may obstruct other command designs
        """
        obstructions[command_name] = self.compute_obstructions_with_definitive_texts_for_cmd_obstruction(obstructions, command_dicts, command_name, definitive_texts, logit)
        definitive_texts[command_name], direction = self.compute_definitive_texts_for_cmd_obstruction(obstructions, command_dicts, command_name, logit)
        
        return self.hide_text_obstructing(command_dicts, command_name, direction, obstructions, definitive_texts, logit)
    
    def hide_text_obstructing_definite_text(self, command_name, command_dicts, obstructions, definitive_texts, logit=logging.info) :
        """
        Hide the texts that may obstruct the definitive text of other commands
        """
        obstructions[command_name] = self.compute_obstructions_with_definitive_texts_for_text_obstruction(obstructions, command_dicts, command_name, definitive_texts, logit)
        definitive_texts[command_name], direction = self.compute_definitive_texts_for_text_obstruction(obstructions, command_dicts, command_name, logit)
        
        return self.hide_text_obstructing(command_dicts, command_name, direction, obstructions, definitive_texts, logit)
        
    def hide_text_obstructing(self, command_dicts, command_name, direction, obstructions, definitive_texts, logit=logging.info) :
        """
        Invoke the 'hide_other_text' function and returns the remaining obstructions
        """
        if direction != None :
            self.hide_other_texts(direction, command_dicts, command_name, logit)
            
        # At this point, all the texts that may obstruct other 
        # commands without having any else space are hidden
        # obstructions = {cmd: {dir: obstructions[cmd][dir] for dir in obstructions[cmd]} for cmd in ordered_commands if definitive_texts[cmd] == None}
        obstructions = {cmd: {dir: obstructions[cmd][dir] for dir in obstructions[cmd] if obstructions[cmd][dir]!=True} for cmd in command_dicts.keys() if definitive_texts[cmd] == None}
        return obstructions, definitive_texts
        
    def hide_text(self, command_dicts, command_name, direction, logit=logging.info):
        """
        Hide the text in the given direction
        """
        text_box = command_dicts[command_name]["text_boxes"][direction]["xml"]
        text_box.set("style", "display:none")
        background_text_box = command_dicts[command_name]["background_text_boxes"][direction]["xml"]
        background_text_box.set("style", "display:none")

    def hide_other_texts(self, direction, command_dicts, command_name, logit=logging.info) :
        """
        Hide the texts that are not in the chosen direction
        """
        text_boxes = command_dicts[command_name]["text_boxes"]
        for other_direction in text_boxes.keys() :
            if other_direction != direction :
                text_box = text_boxes[other_direction]["xml"]
                text_box.set("style", "display:none")
                
        background_text_box = command_dicts[command_name]["background_text_boxes"]
        for other_direction in background_text_box.keys() :
            if other_direction != direction :
                text_box = background_text_box[other_direction]["xml"]
                text_box.set("style", "display:none")
    
    def compute_collision_with_commands(self, command_dicts, direction, command_name, logit=logging.info) :
        """
        Compute the collision of a text with other commands
        """            
        text_boxes = command_dicts[command_name]["text_boxes"]
        other_command_icons = {c_name: command_dicts[c_name]["icon"] for c_name in command_dicts.keys() if c_name != command_name}
        
        text_box = text_boxes[direction]["box"]
        max_width = float(self.document.getroot().get("width")[:-2])
        max_height = float(self.document.getroot().get("height")[:-2])
        
        # Ensure that the text box is not outside the document 
        if text_box[0][0] < 0 or text_box[0][1] < 0 or text_box[1][0] > max_width or text_box[1][1] > max_height :
            return True
        else :
            for other_command in other_command_icons.keys() :
                if other_command != command_name :
                    other_command_disk = other_command_icons[other_command]
                    if self.intersect(other_command_disk, text_box, logit) :
                        return True
        return False
        
    def intersect(self, circle, text_box, logit=logging.info) :
        """
        Return True if the circle intersects the text box
        """
        r = float(circle.get("r"))
        cx = float(circle.get("cx"))
        cy = float(circle.get("cy"))
        x1 = text_box[0][0]
        y1 = text_box[0][1]
        x2 = text_box[1][0]
        y2 = text_box[1][1]
 
        # Find the nearest point on the 
        # rectangle to the center of 
        # the circle
        xn = max(x1, min(cx, x2))
        yn = max(y1, min(cy, y2))
        
        # Find the distance between the 
        # nearest point and the center 
        # of the circle
        # Distance between 2 points, 
        # (x1, y1) & (x2, y2) in 
        # 2D Euclidean space is
        # ((x1-x2)**2 + (y1-y2)**2)**0.5
        Dx = xn - cx
        Dy = yn - cy
        
        return (Dx**2 + Dy**2) <= r**2
    
    def collide(self, text_box1, text_box2, logit=logging.info) :
        """
        Check if two text boxes collide.
        """
        top_left_box1 = text_box1[0]
        top_right_box1 = np.array([text_box1[1][0], text_box1[0][1]])
        bottom_left_box1 = np.array([text_box1[0][0], text_box1[1][1]])
        bottom_right_box1 = text_box1[1]
        
        top_left_box2 = text_box2[0]
        top_right_box2 = np.array([text_box2[1][0], text_box2[0][1]])
        bottom_left_box2 = np.array([text_box2[0][0], text_box2[1][1]])
        bottom_right_box2 = text_box2[1]
        
        # Check if the boxes intersect
        top_left_box1_in_box2 = self.in_box(top_left_box1, text_box2)
        top_right_box1_in_box2 = self.in_box(top_right_box1, text_box2)
        bottom_left_box1_in_box2 = self.in_box(bottom_left_box1, text_box2)
        bottom_right_box1_in_box2 = self.in_box(bottom_right_box1, text_box2)
        
        top_left_box2_in_box1 = self.in_box(top_left_box2, text_box1)
        top_right_box2_in_box1 = self.in_box(top_right_box2, text_box1)
        bottom_left_box2_in_box1 = self.in_box(bottom_left_box2, text_box1)
        bottom_right_box2_in_box1 = self.in_box(bottom_right_box2, text_box1)
        
        return top_left_box1_in_box2 or top_right_box1_in_box2 or bottom_left_box1_in_box2 or bottom_right_box1_in_box2 or top_left_box2_in_box1 or top_right_box2_in_box1 or bottom_left_box2_in_box1 or bottom_right_box2_in_box1
    
    def in_box(self, point, box) :
        """
        Check if a point is in a box
        """
        return box[0][0] <= point[0] <= box[1][0] and box[0][1] <= point[1] <= box[1][1]        
    
    def compute_collision_with_paths(self, text_box, paths, logit=logging.info) :
        """
        Compute the collision of a text with designs
        """
        hitbox_distance = text_box[1][1] - text_box[0][1]
        
        hitbox_textbox = [text_box[0] - np.array([hitbox_distance, hitbox_distance]), text_box[1] + np.array([hitbox_distance, hitbox_distance])]
        
        close_points=0
        for path in paths :
            previous_point = [None,None]
            for point in path:
                if hitbox_textbox[0][0] <= point[0] <= hitbox_textbox[1][0] and hitbox_textbox[0][1] <= point[1] <= hitbox_textbox[1][1] or self.in_segment(previous_point, point, hitbox_textbox, logit) :
                    close_points += 1
                previous_point = point
        
        return close_points
    
    def in_segment(self, previous_point, point, hitbox_textbox, logit=logging.info) :
        """
        Evaluate if a point is in a segment
        """
        # Check if previous point has None values
        if previous_point[0] != None and previous_point[1] != None :
            # We want to check if the segment [previous_point, point] intersects the hitbox
            # We first check if the segment intersects the vertical lines of the hitbox
            if previous_point[0] <= hitbox_textbox[0][0] <= point[0] or previous_point[0] <= hitbox_textbox[1][0] <= point[0] :
                # The segment intersects the vertical lines of the hitbox
                # We then check if the segment intersects the horizontal lines of the hitbox
                if previous_point[1] <= hitbox_textbox[0][1] <= point[1] or previous_point[1] <= hitbox_textbox[1][1] <= point[1] :
                    return True
        return False
        
    def compute_visible_designs(self, document, logit=logging.info) -> list :
        """
        Get all the points of the representations
        Those points are the points of the path of the representation that are visible
        and located under the Designs layer. They have the attribute MREP_PATH_ELEMENT = design
        """
        # Get the Designs layer
        designs_layer = document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)
        # Get the visible layers that are child of the Designs layer
        visible_layers = [child for child in designs_layer[0].getchildren() if child.get("style") != "display:none"]
        # Get the design path for each visible layer
        visible_designs = []
        for layer in visible_layers :
            for child in layer.getchildren() :
                if child.get(u.MREP_PATH_ELEMENT) in [u.DESIGN, u.MULTI_DESIGN] :
                    # Get all points of the path
                    path = svg.path.parse_path(child.get("d"))
                    path_points = [mg.convert_from_complex(path.point(i)) for i in np.linspace(0, 1, 20)]
                    visible_designs.append(path_points)

        # Get the orientation layer
        layer_refs = rf.get_layer_refs(document, False, logit)
        wrist_orientation_layer_refs = rf.get_wrist_orientation_layer_refs(layer_refs, logit)
        orientation_layer = list(wrist_orientation_layer_refs.values())[0]
        # Get the hand layers
        child_paths = orientation_layer.source.findall('.//{*}path')
        visible_hands = []
        for child in child_paths :
            path = svg.path.parse_path(child.get("d"))
            path_points = [mg.convert_from_complex(path.point(i)) for i in np.linspace(0, 1, 20)]
            visible_hands.append(path_points)
        
        return visible_designs, visible_hands
                
    def adapt_icon_command_to_layer(self, layer_ref, mapping_layer, new_command, logit):
        """
        Move the icon command to the layer
        """
        # Find child of layer with MREP_PATH_ELEMENT with 
        # the value of 'icon-command'
        command = layer_ref.source.find(f".//*[@{u.MREP_PATH_ELEMENT}='{u.ICON_COMMAND}']")
        
        if command is not None :
            # Insert the new command above all existing commands and at the placeholded location
            command_layer = self.adapt_command_to_placeholder(command, new_command, logit)
            mapping_layer.insert(0, command_layer)

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
        
        for xml in new_command.findall(".//{*}text") :
            # Adjust the font size
            original_style = xml.get("style")
            style_dict = {style.split(":")[0]:style.split(":")[1] for style in original_style.split(";")}
            font_size = float(style_dict["font-size"][:-2])
            new_font_size = np.round(font_size * factor * 0.90 * np.pow(0.95, int(placeholder_radius - command_radius)), 2)
            new_style_element = {"font-size":f"{new_font_size}px"}
            new_style = compute_new_style(original_style, new_style_element, logit)
            xml.set("style", new_style)
        
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
                correcting_factor = 0.85 * factor
                # Correct by the scaling factor
                New_S_matrix = mg.get_scaling_matrix_from_factor(correcting_factor)
                TRS_matrix = T_placeholder_matrix @ New_S_matrix @ T_origin_matrix 
                # Adjust if the element is the below text
                if xml.get("mgrep-command")=="marker, below":
                    correcting_factor = 1.25 * factor
                    New_S_matrix = mg.get_scaling_matrix_from_factor(correcting_factor)
                    TRS_matrix = T_placeholder_matrix @ New_S_matrix @ T_origin_matrix 
                #     T_marker = mg.get_translation_matrix(np.array([0, -2]), np.array([0, 0]))
                #     TRS_matrix = T_marker @ TRS_matrix 
            else :
                TRS_matrix = T_placeholder_matrix @ T_origin_matrix
                
            circle = mg.apply_matrix_to_circle(circle_coords, [], TRS_matrix, logit)
            xml.set("cx", str(circle[u.COORDINATES].real))
            xml.set("cy", str(circle[u.COORDINATES].imag))
            xml.set("r", str(float(circle[u.CIRCLE_RADIUS])*factor))
            
        return new_command

    def create_command(self, command_name, logit, text=True) :
        """
        Create a command icon with maybe text
        """
        # Copy the template
        new_command_document = etree.fromstring(etree.tostring(self.command_template_ref.source))
        # Get the centroid of the command icon template
        template = new_command_document.xpath('//svg:circle[@mgrep-icon="template"]', namespaces=inkex.NSS)[0]
        
        if text :
            # Sets the command_name for each text
            texts = new_command_document.findall('.//svg:text', namespaces=inkex.NSS)
            for text in texts :
                textspan = text.find('.//svg:tspan', namespaces=inkex.NSS)
                textspan.text = command_name.capitalize()

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
        icon = etree.fromstring(etree.tostring(self.icon_SVG_refs[command_name].source))
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
        if icon_folder_path[-1] != "/" :
            icon_folder_path += "/"
        
        for command in command_names :
            document = etree.parse(f"{icon_folder_path}{command}.svg")
            icon_SVG = rf.get_layer_refs(document, False, logit)[0]
            commands[command] = icon_SVG
            
        return commands

#####################################################################
    
    def compute_visible_points(self, document, logit=logging.info) -> list :
        """
        Get all the points of the representations
        Those points are the points of the path of the representation that are visible
        and located under the Designs layer. They have the attribute MREP_PATH_ELEMENT = design
        """
        # Get the Designs layer
        designs_layer = document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)
        # Get the visible layers that are child of the Designs layer
        visible_layers = [child for child in designs_layer[0].getchildren() if child.get("style") != "display:none"]
        # Get the design path for each visible layer
        design_points = []
        for layer in visible_layers :
            for child in layer.getchildren() :
                if child.get(u.MREP_PATH_ELEMENT) in [u.DESIGN, u.MULTI_DESIGN] :
                    # Get all points of the path
                    path = svg.path.parse_path(child.get("d"))
                    path_points = [mg.convert_from_complex(path.point(i)) for i in np.linspace(0, 1, 20)]
                    design_points += path_points
        self.visible_points = design_points
                    
    def get_markers(self, document, logit) -> list :
        """
        Get all positions of the elements having the attribute 'mgrep-marker'
        """
        svg_layers = document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        
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

    def get_active_markers_positions(self, document, logit) -> list :
        """
        Get all the text_box positions in the SVG
        """
        svg_circles = document.xpath('//svg:circle', namespaces=inkex.NSS)
        
        # Get only the active markers
        active_markers = []
        for circle in svg_circles :
            if circle.get('mgrep-status')=='active' :
                position = np.array([float(circle.get('cx')), float(circle.get('cy'))])
                active_markers.append(position)
        
        return active_markers

    def get_icon_positions(self, document, logit) -> list :
        """
        Get all the icon positions in the SVG
        """
        # Get Designs layer
        designs_layer = document.xpath('//svg:g[@inkscape:label="Designs"]', namespaces=inkex.NSS)
        
        # Get circles in the Designs layer
        svg_circles = designs_layer[0].xpath('.//svg:circle', namespaces=inkex.NSS)
        
        icons = []
        for circle in svg_circles :
            if circle.get(u.MREP_PATH_ELEMENT)==u.COMMAND:
                position = np.array([float(circle.get('cx')), float(circle.get('cy'))])
                icons.append(position)
        
        return icons
    
    def set_commands_radius(self, document, mapping, radius, logit) :
        """
        Set the radius of the commands
        """
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = rf.get_layer_refs(document, False, logit)
        mg_layer_refs = rf.get_mg_layer_refs(layer_refs, logit)
        
        command_circles = []
        for fmc, command in mapping :
            finger, mg, charac = fmc
            for layer_ref in mg_layer_refs[finger][mg][charac] :
                # Check if the layer and all its parents are visible
                if not layer_ref.is_visible() :
                    continue
                
                circle = layer_ref.source.find(f".//*[@{u.MREP_PATH_ELEMENT}='{u.COMMAND}']")
                
                if circle is not None :
                    command_circles.append(circle)
        
        for circle in command_circles :
            circle.set('r', str(radius))
        
        # Make sure commands do not overlap
        for i, circle1 in enumerate(command_circles) :
            for circle2 in command_circles[i+1:] :
                c1x, c1y, c1r = float(circle1.get('cx')), float(circle1.get('cy')), float(circle1.get('r'))
                c2x, c2y, c2r = float(circle2.get('cx')), float(circle2.get('cy')), float(circle2.get('r'))
                overlap = circles_overlap(c1x, c1y, c1r, c2x, c2y, c2r)

                # Check if there is an overlap between the two distinct circles
                if overlap > 0 and (c1x!=c2x or c1y!=c2y or c1r!=c2r) :
                    # Move the circles so that they do not overlap anymore
                    # Take into account the overlap between them
                    
                    # Get the vector between the two circles
                    vector = np.array([c2x - c1x, c2y - c1y])
                    # Normalize the vector
                    norm_vector = vector/np.linalg.norm(vector)
                    
                    # Get the new positions of the circles
                    new_circle1 = np.array([c1x - norm_vector[0]*overlap, c1y - norm_vector[1]*overlap])
                    new_circle2 = np.array([c2x + norm_vector[0]*overlap, c2y + norm_vector[1]*overlap])
                    
                    # Sets the new positions of the circles
                    circle1.set('cx', str(new_circle1[0]))
                    circle1.set('cy', str(new_circle1[1]))
                    circle2.set('cx', str(new_circle2[0]))
                    circle2.set('cy', str(new_circle2[1]))


#####################################################################

def get_command_names(mappings, logit=logging.info):
    """
    Get all commands in mappings
    Each mapping has the form 
    """
    command_names = list()
    for mapping in mappings :
        for command in get_mapping_commands(mapping, logit) :
            command = command.capitalize()
            if command not in command_names :
                command_names.append(command)
    return command_names
    
def get_text_marker_pairs(command, shift, logit=logging.info):
    """
    Get a list of text and marker pairs
    """
    text_marker_pairs = dict()
    for text in command.findall(".//svg:text", namespaces=inkex.NSS) :
        if 'mgrep-command' in text.attrib :
            text_type =  text.attrib['mgrep-command'].split(",")[1]
            text_type = text_type.replace(" ", "")
            if text_type not in text_marker_pairs :
                text_marker_pairs[text_type] = dict()
            for marker in command.findall(".//svg:circle", namespaces=inkex.NSS) :
                if 'mgrep-command' in marker.attrib :
                    marker_type =  marker.attrib['mgrep-command'].split(",")[1]
                    marker_type = marker_type.replace(" ", "")
                    move_marker_according_to_type(marker, marker_type, shift, logit)
                    if text_type == marker_type :
                        if marker not in text_marker_pairs[text_type] :
                            text_marker_pairs[text_type][marker] = []
                        text_marker_pairs[text_type][marker].append(text)
    return text_marker_pairs

def move_marker_according_to_type(marker, marker_type, shift, logit=logging.info) :
    """
    Move the marker according to its type
    """
    cx = float(marker.get('cx'))
    cy = float(marker.get('cy'))
    # If the marker_type is 'left', move the marker to the left according to the shift
    if marker_type == u.LEFT :
        marker.set('cx', str(cx - shift))
    # If the marker_type is 'right', move the marker to the right according to the shift
    elif marker_type == u.RIGHT :
        marker.set('cx', str(cx + shift))
    # If the marker_type is 'below', move the marker below according to the shift
    elif marker_type == u.BELOW :
        marker.set('cy', str(cy + shift))
    # If the marker_type is 'above', move the marker above according to the shift
    elif marker_type == u.ABOVE :
        marker.set('cy', str(cy - shift))

def compute_text_box(text, marker, marker_type, logit=logging.info) :
    """
    Compute the bounding box of the text
    """
    # Get the textspan which is the child of the text
    textspan = text.find('svg:tspan', namespaces=inkex.NSS)
    # Get the text
    # Get the font size
    styles = text.get('style').split(";")
    # By experience, the real font size is 4 times the font size (don't know why)
    font_size = float([style for style in styles if "font-size" in style][0].split(":")[1][:-2])*2
    # Get the text length
    text_length = len(textspan.text)
    # Get the text height
    font_size_height_ratio = 1.5 # Fixed ratio determined by trial and error on the specific font used
    text_height = font_size / font_size_height_ratio
    # Get the text width (divided by 2 because letters tend to be half as wide as they are tall)
    text_width = text_length * text_height * 0.5
    
    bbox = compute_bbox(marker, marker_type, text_width, text_height, logit)
    return bbox
        
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

def compute_bbox(text_marker, text_direction, width, height, logit=logging.info) :
    """
    Compute the bounding box of the text
    """
    marker_pos = np.array([float(text_marker.get('cx')), float(text_marker.get('cy'))])
    
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

def has_main_command_icon(layer_ref) :
    """
    Check if the layer has a command
    """
    return layer_ref.source.find(f".//*[@{u.MREP_PATH_ELEMENT}='{u.COMMAND}']") is not None

def has_duplicated_command_icon(layer_ref) :
    """
    Check if the layer has an icon-command
    """
    return layer_ref.source.find(f".//*[@{u.MREP_PATH_ELEMENT}='{u.ICON_COMMAND}']") is not None

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
    for text in cmd.findall('.//svg:text', namespaces=inkex.NSS) :
        textspan = text.find('.//svg:tspan', namespaces=inkex.NSS)
        # Set command name with capitalized first letter
        textspan.text = f"{mg_text.upper()} {textspan.text}"

def circles_overlap(c1x, c1y, c1r, c2x, c2y, c2r):
    distance = ((c1x - c2x)**2 + (c1y - c2y)**2)**0.5

    return  (c1r + c2r) - distance
        
#####################################################################

#####################################################################

def _main():
    effect = MapCommands()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#######################################################################################################################