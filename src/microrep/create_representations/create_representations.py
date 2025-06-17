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
from inkex.elements import Group

import microrep.core.export as ex
import microrep.core.mg_maths as mg
import microrep.core.ref_and_specs as rf
import microrep.core.utils as u
from microrep.create_representations.configuration_file import *
from microrep.create_representations.create_mg_rep import *

#####################################################################

class CreateRepresentations(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """
    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument("--prefix", type=str, dest="prefix", default="", help='Prefix to add to the exported file name')
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='svg', 
                                     help='Exported file type. One of [svg|png|jpg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image (if applicable)")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export")
        self.arg_parser.add_argument("--family", type=str, dest="family", default="AandB", help="Selected family")
        self.arg_parser.add_argument("--traces", type=inkex.Boolean, dest="traces", default=False, help='Show traces')
        self.arg_parser.add_argument("--command", type=inkex.Boolean, dest="command", default=False, help='Show command placeholders')
        self.arg_parser.add_argument("--radius", type=float, dest="radius", default=2.5, help="Command expected radius")
        self.arg_parser.add_argument("--one_trajectory_only", type=inkex.Boolean, dest="one_trajectory_only", default=True, help="Depicts one trajectory at max to avoid cluttering (default: True)")
        self.arg_parser.add_argument("--four", type=inkex.Boolean, dest="four", default=False, help='Stop after processing the four first representations of a family')
        self.arg_parser.add_argument("--one", type=inkex.Boolean, dest="one", default=False, help='Stop after processing one family')
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
        self.arg_parser.add_argument("--dry", type=inkex.Boolean, dest="dry", default=False, help="Don't actually do all of the exports")
    
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
    
        # Get a dictionnary of the wanted microgestures-combinations with their characteristics
        combinations = get_combinations(self.options.config, logit)
        
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = rf.get_layer_refs(self.document, False, logit)
        wrist_orient_refs = rf.get_wrist_orientation_layer_refs(layer_refs, logit)
        logit(f"Found {len(wrist_orient_refs)} wrist orientation layers")
        if len(wrist_orient_refs) != 1:
            logit(f"Error: expected exactly one wrist orientation layer, found {len(wrist_orient_refs)}")
            return
        else:
            wrist_orient = list(wrist_orient_refs.keys())[0]
            
        family_layer_refs = rf.get_family_layer_refs(layer_refs, logit)
        
        # Get a dictionnary of each wanted microgesture marker
        # with their positions put in a dictionnary according to their type
        marker_layer_refs = rf.get_marker_layer_refs(layer_refs, logit)
        markers = rf.get_markers_pos(marker_layer_refs[wrist_orient], logit)
        # Hide the marker layers forever
        rf.hide_marker_layers(marker_layer_refs, logit)
        # Hide the family layers temporarily
        rf.hide_family_layers(family_layer_refs, self.options.traces, self.options.command)
        
        # Create the Design layer above all the other layers
        self.design_layer = self.create_design_layer()
        family = self.options.family
        representation_layers = {u.get_combination_name(combination): dict()for combination in combinations}
        
        if family in family_layer_refs:
            self.register_family(family, family_layer_refs, representation_layers, combinations, markers, logit)
        else :
            logit(f"Error: family {family} not found. Exporting all families")
            for family in family_layer_refs:
                break_bool = self.register_family(family, family_layer_refs, representation_layers, combinations, markers, logit)
                if break_bool:
                    break
                
        self.export_representations(representation_layers, combinations, logit)
        
        # Delete layer with label "Design"
        self.design_layer.delete()
        
        rf.show_family_layers(family_layer_refs)
        rf.show_marker_layers(marker_layer_refs, logit)
    
    def register_family(self, family, family_layer_refs, representation_layers, combinations, markers, logit=logging.info) :
        """
        Register the representation layers corresponding to the family 
        """
        counter=1
        logit(f"Exporting {family} family\n")
        for combination in combinations:
            combination_name = u.get_combination_name(combination)
            mp_finger, mp_charac = u.get_most_proximate_finger_and_charac_for_tap(combination, logit)
            representation_layers[combination_name][family] = dict()
            
            for finger, mg, charac in combination :
                logit(f"Creating {mg}-{charac} layers\n")
                created_layers = list()
                # Duplicate the family layers to create the representation
                if mg in family_layer_refs[family] and charac in family_layer_refs[family][mg]:
                    for element in family_layer_refs[family][mg][charac] :
                        # Draw trajectory only if its the index tip (Avoid trajectory overlapping other trajectories)
                        if to_draw(finger, mg, charac, element, mp_finger, mp_charac, self.options.one_trajectory_only):
                            new_layer_name = f"{family}_{finger}_{mg}_{charac}_{element}"
                            family_layer_ref = family_layer_refs[family][mg][charac][element]
                            new_family_layer = self.duplicate_family_layer(family_layer_ref, new_layer_name)
                                                        
                            # Create the family element depending on the marker's position
                            logit(f"Creating the layer : {new_layer_name}")
                            specific_markers = markers[finger][mg][charac]
                            if mg==u.SWIPE:
                                multi_design = False
                                # We can select only the multi-design if it exists
                                paths = [path.get(u.MREP_PATH_ELEMENT) for path in new_family_layer.findall('.//{*}path')]
                                if u.MULTI_DESIGN in paths:
                                    # Here we need to check if the two opposite directions are being represented in the combination
                                    for _, other_mg, other_charac in combination:
                                        if other_mg==u.SWIPE and other_charac in u.OPPOSITE_SWIPE_CHARACTERISTICS[charac]:
                                            # If that case, the opposite direction is represented
                                            multi_design = True
                                
                                create_mg_rep(new_family_layer, element, specific_markers, self.options.radius, multi_design, logit=logit)
                            else:
                                create_mg_rep(new_family_layer, element, specific_markers, logit=logit)
                            
                            # Adds the 'mgrep-microgesture-layer' attribute to the layer 
                            # It can be used later to diversify the representation 
                            # according to the microgesture and is used to associate
                            # the commands to their placeholders
                            new_family_layer.set(rf.MicrogestureExportSpec.ATTR_ID, f"{finger}, {mg}, {charac}")
                            new_family_layer.set(rf.MicrogestureExportSpec.ELEMENT_ID, f"{element}")
                            
                            created_layers.append(new_family_layer)
                
                # Adding the representation to the dictionnary
                if finger not in representation_layers[combination_name][family] :
                    representation_layers[combination_name][family][finger] = dict()
                if mg not in representation_layers[combination_name][family][finger] :
                    representation_layers[combination_name][family][finger][mg] = dict()
                if charac not in representation_layers[combination_name][family][finger][mg] :
                    representation_layers[combination_name][family][finger][mg][charac] = dict()
                representation_layers[combination_name][family][finger][mg][charac] = created_layers
                
                # Break on 4 first microgestures for debug purposes
                if self.options.four and counter>=4:
                    return True
                counter+=1
                
            # Break on first family for debug purposes
            if self.options.one:
                return True
        
        return False  

#####################################################################
        
    def create_design_layer(self) :
        """
        Creates the layer that will handle all the legends
        It is placed above all the existing layers to be visible
        """
        design_layer = Group.new('Designs', is_layer=True)
        design_layer.set("id", "designs-layer")
        # Add legend layer to the document
        self.document.getroot().append(design_layer)
        return design_layer
    
    def duplicate_family_layer(self, source_layer_ref, layer_label):
        """
        Copy a layer and returns the new layer
        """
        new_layer = self.svg.add(source_layer_ref.source.copy())
        new_layer.set("id", self.svg.get_unique_id("layer"))
        new_layer.label = layer_label
        new_layer.style = 'display:none'
        
        # Add to design layer
        self.design_layer.insert(0, new_layer)
                
        return new_layer

    def export_representations(self, representation_layers, combinations, logit=logging.info) :
        """
        Exports the representations corresponding to the combinations
        using the previously computed representation layers 
        """
        for combination in combinations:
            combination_name = u.get_combination_name(combination)
            for family in representation_layers[combination_name] :
                combinated_representations = list()
                for finger, mg, charac in combination :
                    combinated_representations.append(representation_layers[combination_name][family][finger][mg][charac])
                self.export_combination(f"{family}_{combination_name}", combinated_representations, logit)

    def export_combination(self, label, combinated_representations, logit=logging.info) :
        """
        Exports the image with the created layers visible all at once
        """
        label = f"{label}"
            
        # Make sure the created layers are visible
        for representation_layers in combinated_representations :
            show_layers(representation_layers)
            
                
        # Skip the export if --dry was specified
        if self.options.dry:
            logit(f"Skipping {label} export because --dry was specified")
        else :
            # Actually do the export into the destination path.
            ex.export(self.document, label, self.options, logit)

        # Make sure the created layers are visible
        for representation_layers in combinated_representations :
            hide_layers(representation_layers)

#####################################################################
 
def show_layers(layers) :
    """
    Show the given layers
    """
    for layer in layers :
        layer.attrib['style'] = 'display:inline'
        
def hide_layers(layers) :
    """
    Show the given layers
    """
    for layer in layers :
        layer.attrib['style'] = 'display:none'

def delete_created_layers(representation_layers):
    """
    Delete all the layers contained in representations
    """
    for family in representation_layers :
        for mg in representation_layers[family] :
            for charac in representation_layers[family][mg] :
                for layer in representation_layers[family][mg][charac] :
                    layer.delete()
    
def to_draw(finger, mg, charac, element, mp_finger, mp_charac, one_trajectory_only):
    """
    Returns True if the trajectory should be drawn
    """
    return (not one_trajectory_only and finger==u.INDEX) or not (mg!=u.SWIPE and element==u.TRAJECTORY and (finger!=mp_finger or charac!=mp_charac))
                    
#####################################################################

def _main():
    effect = CreateRepresentations()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#####################################################################
