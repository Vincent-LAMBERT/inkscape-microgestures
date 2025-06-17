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
import logging
import os
import subprocess
import tempfile

import inkex

import microrep.core.export as ex
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.scale_mg_rep as sc
import microrep.core.utils as u
from microrep.add_enhancement.configuration_file import *

#####################################################################

class AddEnhancement(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export")
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
        
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = rf.get_layer_refs(self.document, False, logit)
        mg_layer_refs = rf.get_mg_layer_refs(layer_refs, logit)
        
        # Get a dictionnary of the wanted diversified styles with their characteristics
        combinated_styles = get_combinations(self.options.config, logit)
        for style in combinated_styles :
            change_styles(mg_layer_refs, style[u.COMBINATION], logit)
            # Actually do the export into the destination path.
            splitted_svg_name = self.svg_name.split("_")
            family_name = splitted_svg_name[0]
            # Join the name of the svg file without the family name
            mg_characs = "_".join(splitted_svg_name[1:])
            mg_characs = mg_characs.replace(".svg", "")
            logit(f"Exporting {family_name}@{style[u.NAME]}_{mg_characs}")
            ex.export(self.document, f"{family_name}@{style[u.NAME]}_{mg_characs}", self.options, logit)
            reset_styles(mg_layer_refs)

#####################################################################

def change_styles(mg_layer_refs, style_combination, logit=logging.info) :
    """
    Change the style of the elements in the layers
    """
    for finger in mg_layer_refs :
        for mg in mg_layer_refs[finger] :
            for charac in mg_layer_refs[finger][mg] :
                for layer_ref in mg_layer_refs[finger][mg][charac] :
                    # Get the microgesture described by the children
                    mg_styles = get_mg_associated_styles(mg, style_combination, logit)
                    # Get each element of the layer
                    for child in layer_ref.source.getchildren() :
                        # Check if the element is a design element
                        if (child.tag == inkex.addNS('path','svg') or child.tag == inkex.addNS('circle','svg')) and child.attrib[u.MREP_PATH_ELEMENT] in [u.DESIGN, u.MULTI_DESIGN] :
                            # Get the child style
                            if child not in layer_ref.non_layer_children_style :
                                layer_ref.non_layer_children_style[child.get("id")] = child.get("style")
                            original_style = layer_ref.non_layer_children_style[child.get("id")]
                            new_style = compute_new_style(original_style, mg_styles, logit)
                            child.set("style", new_style)
                        
                        if child.attrib[u.MREP_PATH_ELEMENT] in [u.DESIGN, u.MULTI_DESIGN, u.TRACE] and (u.PATH_SCALE in mg_styles or u.STROKE_WIDTH in mg_styles) :
                            if child.tag == inkex.addNS('path','svg') :
                                if u.PATH_SCALE in mg_styles :
                                    scaling = float(mg_styles[u.PATH_SCALE])
                                elif u.STROKE_WIDTH in mg_styles :
                                    scaling = float(mg_styles[u.STROKE_WIDTH])
                                layer_ref.non_layer_children_initial_path[child.get("id")] = child.get("d")
                                scale_child(layer_ref, child, scaling, logit)
                            
                            if child.tag == inkex.addNS('circle','svg') :
                                if u.PATH_SCALE in mg_styles :
                                    scaling = float(mg_styles[u.PATH_SCALE])
                                elif u.STROKE_WIDTH in mg_styles :
                                    scaling = float(mg_styles[u.STROKE_WIDTH])
                                layer_ref.non_layer_children_initial_path[child.get("id")] = child.get("r")
                                child.set("r", str(float(child.get("r"))*scaling))

def reset_styles(mg_layer_refs) :
    """
    Reset the style of the elements in the layers
    """
    for finger in mg_layer_refs :
        for mg in mg_layer_refs[finger] :
            for charac in mg_layer_refs[finger][mg] :
                for layer_ref in mg_layer_refs[finger][mg][charac] :
                    for child in layer_ref.source.getchildren() :# Check if the element is a design element
                        if (child.tag == inkex.addNS('path','svg') or child.tag == inkex.addNS('circle','svg')) and child.attrib[u.MREP_PATH_ELEMENT] in [u.DESIGN, u.MULTI_DESIGN] :
                            # Get the child style
                            original_style = layer_ref.non_layer_children_style[child.get("id")]
                            child.set("style", original_style)
                            
                        if child.attrib[u.MREP_PATH_ELEMENT] in [u.DESIGN, u.MULTI_DESIGN] :
                            if child.get("id") in layer_ref.non_layer_children_initial_path :
                                if child.tag == inkex.addNS('path','svg') :
                                    child.set("d", layer_ref.non_layer_children_initial_path[child.get("id")])
                                if child.tag == inkex.addNS('circle','svg') :
                                    child.set("r", layer_ref.non_layer_children_initial_path[child.get("id")])
                                    
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
                
def get_element_style(element) :
    """
    Parse the style of a SVG element and
    put each element in a dictionnary
    """
    styles = dict()
    string_style = element.get("style")
    for style in string_style.split(";") :
        if style != "" :
            key, value = style.split(":")
            styles[key] = value

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

#####################################################################

def _main():
    effect = AddEnhancement()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()