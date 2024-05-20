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

import logging
import inkex
import numpy as np

from .utils import *
from lxml import etree


#####################################################################

def get_layer_refs(document, visible_only=False, logit=logging.info) -> list:
    """
    Return the layers in the SVG
    """
    svg_layers = document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
    # logit(f"\n svg_layers : {svg_layers}")
    layer_refs = []

    # Find all of our "valid" layers.
    for layer in svg_layers:
        if visible_only and "style" in layer.attrib and layer.attrib["style"] == "display:none":
            continue
        label_attrib_name = LayerRef.get_layer_attrib_name(layer)
        if label_attrib_name not in layer.attrib:
            continue
        layer_refs.append(LayerRef(layer, logit))

    # Create the layer hierarchy (children and parents).
    for layer in layer_refs:
        for other in layer_refs:
            for child in layer.source.getchildren():
                if child is other.source:
                    layer.children.append(other)
            if layer.source.getparent() is other.source:
                layer.parent = other

    return layer_refs

def get_family_layer_refs(layer_refs, logit=logging.info) :
    """
    Retrieve the family layers
    """
    family_layer_refs = dict()
    # Figure out the family layers.
    for layer_ref in layer_refs:
        if not layer_ref.has_valid_family_export_spec():
            continue
        
        for export in layer_ref.family_export_specs :
            if export.family not in family_layer_refs:
                # logit(f"Found valid family '{export.family}'")
                family_layer_refs[export.family] = dict()
            if export.microgesture not in family_layer_refs[export.family] :
                family_layer_refs[export.family][export.microgesture] = dict()
            if export.characteristic not in family_layer_refs[export.family][export.microgesture] :
                family_layer_refs[export.family][export.microgesture][export.characteristic] = dict()
            family_layer_refs[export.family][export.microgesture][export.characteristic][export.element] = layer_ref

    logit(f"Found {len(family_layer_refs)} valid families : {list(family_layer_refs.keys())}")
    return family_layer_refs

def get_commands_with_positions(mg_layer_refs, logit=logging.info) :
    """
    Retrieve the commands positions alongside the commands
    """
    commands = dict()
    for finger in mg_layer_refs.keys() :
        for mg in mg_layer_refs[finger].keys() :
            for charac in mg_layer_refs[finger][mg].keys() :
                layer_refs = mg_layer_refs[finger][mg][charac]
                for layer_ref in layer_refs :
                    # Check if the layer is visible to consider its command
                    layer = layer_ref.source
                    if layer.get('style') != 'display:none' :
                        if finger not in commands :
                            commands[finger] = dict()
                        if mg not in commands[finger] :
                            commands[finger][mg] = dict()
                        if charac not in commands[finger][mg] :
                            commands[finger][mg][charac] = []
                        # Get the command in layer_ref childrens
                        for child in layer_ref.source.getchildren() :
                            # Check if there is an attribute mgrep-path-element with value equal to COMMAND
                            if 'mgrep-path-element' in child.attrib and child.attrib['mgrep-path-element'] == COMMAND :
                                child_position = [np.round(float(child.get('cx')),4), np.round(float(child.get('cy')),4)]
                                commands[finger][mg][charac] = (child, child_position)
    
    return commands

def get_mg_layer_refs(layer_refs, logit=logging.info) :
    """
    Retrieve the microgesture layers
    """
    count=0
    mg_layer_refs = dict()
    # Figure out the family layers.
    for layer_ref in layer_refs:
        if not layer_ref.has_valid_mg_export_spec():
            continue
        
        for export in layer_ref.mg_export_specs :
            if export.finger not in mg_layer_refs :
                mg_layer_refs[export.finger] = dict()
            if export.microgesture not in mg_layer_refs[export.finger] :
                mg_layer_refs[export.finger][export.microgesture] = dict()
            if export.characteristic not in mg_layer_refs[export.finger][export.microgesture] :
                mg_layer_refs[export.finger][export.microgesture][export.characteristic] = list()
            count+=1
            mg_layer_refs[export.finger][export.microgesture][export.characteristic].append(layer_ref)

    logit(f"Found {count} valid layers for {len(mg_layer_refs)} types of microgestures")
    return mg_layer_refs
    
def get_marker_layer_refs(layer_refs, logit=logging.info) :
    """
    Retrieve the marker layers
    """
    counter=0
    marker_layer_refs = dict()
    # Figure out the marker layers.
    for layer_ref in layer_refs:
        if not layer_ref.has_valid_marker_export_spec():
            continue
        else :
            for export in layer_ref.marker_export_specs :
                # logit(f"Found valid marker : {export.microgesture}, {export.characteristic}, {export.markerType}")
                if export.finger not in marker_layer_refs:
                    marker_layer_refs[export.finger] = dict()
                if export.microgesture not in marker_layer_refs[export.finger]:
                    marker_layer_refs[export.finger][export.microgesture] = dict()
                if export.characteristic not in marker_layer_refs[export.finger][export.microgesture]:
                    marker_layer_refs[export.finger][export.microgesture][export.characteristic] = dict()
                marker_layer_refs[export.finger][export.microgesture][export.characteristic][export.markerType] = layer_ref
                counter+=1

    logit(f"Found {counter} valid markers")
    return marker_layer_refs

def get_wrist_orientation_layer_refs(layer_refs, logit=logging.info) :
    """
    Retrieve the wrist orientation layers
    """
    counter=0
    wrist_orientation_layer_refs = dict()
    # Figure out the hand pose layers.
    for layer_ref in layer_refs:
        if not layer_ref.has_valid_wrist_orientation_export_spec() :
            continue
        elif layer_ref.has_valid_finger_status_export_spec() :
            continue
        else :
            for export in layer_ref.wrist_orientation_export_specs :
                wrist_orientation_layer_refs[export.wrist_orientation] = layer_ref
                counter+=1

    logit(f"Found {counter} valid wrist orientations")
    logit(f"Wrist orientations : {wrist_orientation_layer_refs}")
    return wrist_orientation_layer_refs

def get_finger_pose_layer_refs(layer_refs, logit=logging.info) :
    """
    Retrieve the finger pose layers
    """
    counter=0
    finger_status_layer_refs = dict()
    # Figure out the hand pose layers.
    for layer_ref in layer_refs :
        if not layer_ref.has_valid_finger_status_export_spec() :
            continue
        elif layer_ref.has_valid_finger_status_export_spec() and layer_ref.has_valid_wrist_orientation_export_spec() :

            for wrist_export in layer_ref.wrist_orientation_export_specs :
                if wrist_export.wrist_orientation not in finger_status_layer_refs:
                    finger_status_layer_refs[wrist_export.wrist_orientation] = dict()

                for finger_export in layer_ref.finger_status_export_specs :
                    if finger_export.finger not in finger_status_layer_refs[wrist_export.wrist_orientation]:
                        finger_status_layer_refs[wrist_export.wrist_orientation][finger_export.finger] = dict()
                    finger_status_layer_refs[wrist_export.wrist_orientation][finger_export.finger][finger_export.status] = layer_ref
                    counter+=1
        else :
            logit(f"Layer {layer_ref.label} has an invalid combination of wrist orientation and finger status")

    logit(f"Found {counter} valid finger status")
    logit(f"Finger status : {finger_status_layer_refs}")
    return finger_status_layer_refs

def get_markers_pos(marker_layer_refs, logit=logging.info) :
    """
    Retrieve the markers positions
    """    
    markers = dict()
    for finger in marker_layer_refs.keys() :
        markers[finger] = dict()
        for mg in marker_layer_refs[finger].keys() :
            markers[finger][mg] = dict()
            for charac in marker_layer_refs[finger][mg].keys() :
                markers[finger][mg][charac] = dict()
                for markerType in marker_layer_refs[finger][mg][charac].keys() :
                    markers[finger][mg][charac][markerType] = []
                    layer_ref = marker_layer_refs[finger][mg][charac][markerType]
                    # Get the marker in layer_ref childrens
                    if 'mgrep-marker' in layer_ref.source.attrib :
                        marker = layer_ref.source.getchildren()[0]
                        marker_position = [np.round(float(marker.get('cx')),4), np.round(float(marker.get('cy')),4)]
                        markers[finger][mg][charac][markerType] = (marker, marker_position)
    return markers

def show_marker_layers(marker_layer_refs) :
    """
    Show the markers
    """
    for finger in marker_layer_refs :
        for microgesture in marker_layer_refs[finger] :
            for characteristic in marker_layer_refs[finger][microgesture] :
                for markerType in marker_layer_refs[finger][microgesture][characteristic] :
                    layer = marker_layer_refs[finger][microgesture][characteristic][markerType]
                    layer.source.attrib['style'] = 'display:inline'

def hide_marker_layers(marker_layer_refs) :
    """
    Hide the markers
    """
    for finger in marker_layer_refs :
        for microgesture in marker_layer_refs[finger] :
            for characteristic in marker_layer_refs[finger][microgesture] :
                for markerType in marker_layer_refs[finger][microgesture][characteristic] :
                    layer = marker_layer_refs[finger][microgesture][characteristic][markerType]
                    layer.source.attrib['style'] = 'display:none'

def show_family_layers(family_layer_refs) :
    """
    Show the family elements
    """
    for family in family_layer_refs :
        for microgesture in family_layer_refs[family] :
            for characteristic in family_layer_refs[family][microgesture] :
                for element in family_layer_refs[family][microgesture][characteristic] :
                    layer = family_layer_refs[family][microgesture][characteristic][element]
                    layer.source.attrib['style'] = 'display:inline'
                    # Hide the command and trace paths forever
                    show_trace_path(layer)
                    show_command_path(layer)

def hide_family_layers(family_layer_refs, show_trace_path=False, show_command_path=False) :
    """
    Hide the family elements
    """
    for family in family_layer_refs :
        for microgesture in family_layer_refs[family] :
            for characteristic in family_layer_refs[family][microgesture] :
                for element in family_layer_refs[family][microgesture][characteristic] :
                    layer = family_layer_refs[family][microgesture][characteristic][element]
                    layer.source.attrib['style'] = 'display:none'
                    # Hide the command and trace paths forever
                    if not show_trace_path :
                        hide_trace_path(layer)
                    if not show_command_path :
                        hide_command_path(layer)
                        
def show_trace_path(layer) :
    """
    Show the trace path
    """
    for child in layer.source.getchildren() :
        if (child.tag == inkex.addNS('path','svg') or inkex.addNS('circle','svg')) : 
            if (child.attrib['mgrep-path-element'] == 'trace'
                or child.attrib['mgrep-path-element'] == 'trace-start-bound'
                or child.attrib['mgrep-path-element'] == 'trace-end-bound') :
                child.attrib['style'] = 'display:inline;fill:none;fill-opacity:1;stroke:#47bd52;stroke-opacity:1'             

def hide_trace_path(layer) :
    """
    Hide the trace path
    """
    for child in layer.source.getchildren() :
        if (child.tag == inkex.addNS('path','svg') or inkex.addNS('circle','svg')) : 
            if (child.attrib['mgrep-path-element'] == 'trace'
                or child.attrib['mgrep-path-element'] == 'trace-start-bound'
                or child.attrib['mgrep-path-element'] == 'trace-end-bound') :
                child.attrib['style'] = 'display:none'

def show_command_path(layer) :
    """
    Show the command path
    """
    for child in layer.source.getchildren() :
        if (child.tag == inkex.addNS('path','svg') or inkex.addNS('circle','svg')) and child.attrib['mgrep-path-element'] == COMMAND :
            child.attrib['style'] = 'display:inline;fill:#f6e90f;fill-opacity:1;stroke:none;stroke-opacity:1'

def hide_command_path(layer) :
    """
    Hide the command path
    """
    for child in layer.source.getchildren() :
        if (child.tag == inkex.addNS('path','svg') or inkex.addNS('circle','svg')) and child.attrib['mgrep-path-element'] == COMMAND :
            child.attrib['style'] = 'display:none'
        
#######################################################################################################################

class LayerRef(object):
    """
    A wrapper around an Inkscape XML layer object plus some helper data for doing combination exports.
    """

    def __init__(self, source: etree.Element, logit=logging.info) :
        self.source = source
        self.id = source.attrib["id"]
        label_attrib_name = LayerRef.get_layer_attrib_name(source)
        self.label = source.attrib[label_attrib_name]
        self.children = list()
        self.non_layer_children_style = dict()
        self.non_layer_children_initial_path = dict()
        self.parent = None

        self.export_specs = list()
        self.request_hidden_state = False
        self.requested_hidden = False
        self.sibling_ids = list()

        self.family_export_specs = FamilyExportSpec.create_specs(self, logit)
        self.mg_export_specs = MicrogestureExportSpec.create_specs(self, logit)
        self.marker_export_specs = MarkerExportSpec.create_specs(self, logit)
        self.wrist_orientation_export_specs = WristOrientationExportSpec.create_specs(self, logit)
        self.finger_status_export_specs = FingerStatusExportSpec.create_specs(self, logit)

    @staticmethod
    def get_layer_attrib_name(layer: etree.Element) -> str:
        return "{%s}label" % layer.nsmap['inkscape']
    
    def has_valid_family_export_spec(self):
        return len(self.family_export_specs) > 0
    
    def has_valid_mg_export_spec(self):
        return len(self.mg_export_specs) > 0
    
    def has_valid_wrist_orientation_export_spec(self):
        return len(self.wrist_orientation_export_specs) > 0
    
    def has_valid_finger_status_export_spec(self):
        return len(self.finger_status_export_specs) > 0
    
    def has_valid_marker_export_spec(self):
        return len(self.marker_export_specs) > 0
    
    def is_visible(self) :
        if self.parent != None :
            return self.parent.attrib["style"] != "display:none" and self.source.attrib["style"] != "display:none"
        return self.source.attrib["style"] != "display:none"
    
    def show_layer(self) :
        if "display:none" in self.source.attrib["style"] :
            self.source.attrib["style"] = self.source.attrib["style"].replace("display:none", "display:inline")
        elif not "display:inline" in self.source.attrib["style"] :
            self.source.attrib["style"] = self.source.attrib["style"] + ";display:inline"

    def hide_layer(self) :
        if "display:inline" in self.source.attrib["style"] :
            self.source.attrib["style"] = self.source.attrib["style"].replace("display:inline", "display:none")
        elif not "display:none" in self.source.attrib["style"] :
            self.source.attrib["style"] = self.source.attrib["style"] + ";display:none"
    
    def __str__(self) -> str:
        return f"LayerRef({self.label}, {self.id}, {self.source})"
    
    def __repr__(self) -> str:
        return str(self)
    
#######################################################################################################################

class FamilyExportSpec(object):
    """
    A description of how to export a family layer.
    """

    ATTR_ID = "mgrep-family-layer"

    def __init__(self, spec: str, layer: object, family: str, element: str, microgesture: str, characteristic: str):
        self.layer = layer
        self.spec = spec
        self.family = family
        self.element = element
        self.microgesture = microgesture
        self.characteristic = characteristic

    @staticmethod
    def create_specs(layer, logit=logging.info) -> list:
        """Extracts '[family],[element]' from the layer's ATTR_ID attribute and returns either an empty list or a list of FamilyExportSpec element. A RuntimeError is raised if it is incorrectly formatted. 
        If the family behaves differently for different microgestures, the microgesture can be specified as well in the format '[family],[element],[microgesture]'.
        This can be detailed one step further with the optionnal characteristic parameter in the format '[family],[element],[microgesture],[characteristic]'.
        """
        result = list()
        if FamilyExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        spec = layer.source.attrib[FamilyExportSpec.ATTR_ID]
        gs_split = spec.split(",")
        if len(gs_split) != 2 and len(gs_split) != 3 and len(gs_split) != 4:
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid form '{gs_split}'. " +
                                f"Expected format is '[family],[element]' or '[family],[element],[microgesture]' or '[family],[element],[microgesture],[characteristic]'.")

        # Removes all whitespaces that could be added for aesthetic reasons
        family = gs_split[0].replace(" ", "")
        element = gs_split[1].replace(" ", "")
        
        if element not in ELEMENTS:
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid element '{element}'. " +
                                f"Only the following are valid: {str(ELEMENTS)}")
        
        # If the microgestures considered for this element are specified
        if len(gs_split) >= 3 :
            microgestures = gs_split[2].split("|")
            for microgesture in microgestures :
                microgesture = microgesture.replace(" ", "")
                if len(gs_split) == 4 :
                    characteristics = gs_split[3].split("|")
                    for characteristic in characteristics :
                        characteristic = characteristic.replace(" ", "")
                        result.append(FamilyExportSpec(spec, layer, family, element, microgesture, characteristic))
                else :
                    for charac in MICROGESTURE_CHARACTERISTICS[microgesture] :
                        result.append(FamilyExportSpec(spec, layer, family, element, microgesture, charac))
                
        else :
            for microgesture in MICROGESTURES :
                for charac in MICROGESTURE_CHARACTERISTICS[microgesture] :
                    result.append(FamilyExportSpec(spec, layer, family, element, microgesture, charac))
        return result
    
    def __str__(self) -> str:
        return f"FamilyExportSpec({self.family}, {self.element}, {self.microgesture}, {self.characteristic})"
    
    def __repr__(self) -> str:
        return str(self)

class MarkerExportSpec(object):
    """
    The description of a marker used to export families with the current representation
    """

    ATTR_ID = "mgrep-marker"

    def __init__(self, spec: str, layer: object, finger: str, microgesture: str, characteristic: str, markerType: str):
        self.layer = layer
        self.spec = spec
        self.finger = finger
        self.microgesture = microgesture
        self.characteristic = characteristic
        self.markerType = markerType

    @staticmethod
    def create_specs(layer, logit=logging.info) -> list:
        """Extracts '[finger][microgesture],[characteristic],[markerType]' from the layer's ATTR_ID attribute and returns either an empty list of one with only one MarkerExportSpec element. A RuntimeError is raised if it is incorrectly formatted. 
        """
        result = list()
        if MarkerExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        spec = layer.source.attrib[MarkerExportSpec.ATTR_ID]
        gs_split = spec.split(",")
        if len(gs_split) != 4:
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid form '{gs_split}'. " +
                                f"Expected format is '[finger][microgesture],[characteristic],[markerType]'")

        # Removes all whitespaces that could be added for aesthetic reasons
        fingers = gs_split[0].split("|")
        for finger in fingers :
            finger = finger.replace(" ", "")
            microgestures = gs_split[1].split("|")
            for microgesture in microgestures :
                microgesture = microgesture.replace(" ", "")
                if microgesture not in MICROGESTURES:
                    raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid microgesture '{microgesture}'. " +
                                f"Only the following are valid: {str(MICROGESTURES)}")
                characteristics = gs_split[2].split("|")
                for characteristic in characteristics :
                    characteristic = characteristic.replace(" ", "")
                    if microgesture==TAP and characteristic not in TAP_CHARACTERISTICS:
                        raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid characteristic '{characteristic}'. " +
                                            f"Only the following are valid with a {microgesture}: {str(TAP_CHARACTERISTICS)}")
                    if microgesture==SWIPE and characteristic not in SWIPE_CHARACTERISTICS:
                        raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid characteristic '{characteristic}'. " +
                                            f"Only the following are valid with a {microgesture}: {str(SWIPE_CHARACTERISTICS)}")
                    if microgesture==FLEX and characteristic not in FLEX_CHARACTERISTICS:
                        raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid characteristic '{characteristic}'. " +
                                            f"Only the following are valid with a {microgesture}: {str(FLEX_CHARACTERISTICS)}")
                    if microgesture==HOLD and characteristic not in HOLD_CHARACTERISTICS:
                        raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid characteristic '{characteristic}'. " +
                                            f"Only the following are valid with a {microgesture}: {str(HOLD_CHARACTERISTICS)}")
                    markerTypes = gs_split[3].split("|")
                    for markerType in markerTypes :
                        markerType = markerType.replace(" ", "")
                        if markerType not in MARKER_TYPES:
                            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid markerType '{markerType}'. " +
                                                f"Only the following are valid: {str(MARKER_TYPES)}")
                        result.append(MarkerExportSpec(spec, layer, finger, microgesture, characteristic, markerType))
        
        return result
    
    def __str__(self) -> str:
        return f"MarkerExportSpec({self.finger}, {self.microgesture}, {self.characteristic}, {self.markerType})"
    
    def __repr__(self) -> str:
        return str(self)

class MicrogestureExportSpec(object):
    """
    A description of how to export a family layer.
    """

    ATTR_ID = "mgrep-microgesture-layer"
    ELEMENT_ID = "mgrep-microgesture-element"

    def __init__(self, spec: str, layer: object, finger : str, microgesture: str, characteristic: str, element: str):
        self.spec = spec
        self.layer = layer
        self.finger = finger
        self.microgesture = microgesture
        self.characteristic = characteristic
        self.element = element

    @staticmethod
    def create_specs(layer, logit=logging.info) -> list:
        """
        Extracts '[finger][microgesture],[characteristic]' from the layer's ATTR_ID attribute 
        and '[element]' from the layer's ELEMENT_ID attribute
        
        Returns either an empty list or a list of FamilyExportSpec element. 
        A RuntimeError is raised if it is incorrectly formatted.
        """
        result = list()
        if MicrogestureExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        spec = layer.source.attrib[MicrogestureExportSpec.ATTR_ID]
        
        g_split = spec.split(",")

        if len(g_split) != 3 :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{spec}'. " +
                                f"Expected value is of the form '[finger][microgesture],[characteristic]'")
        
        finger = g_split[0].replace(" ", "")
        microgesture = g_split[1].replace(" ", "")
        charac = g_split[2].replace(" ", "")
        element = layer.source.attrib[MicrogestureExportSpec.ELEMENT_ID]
        
        if finger not in FINGERS_WITH_THUMB :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{finger}'. " +
                                f"Expected value is one of {list(FINGERS_WITH_THUMB.keys())}")
        if microgesture not in MICROGESTURES :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{microgesture}'. " +
                                f"Expected value is one of {list(MICROGESTURES.keys())}")
        if charac not in MICROGESTURE_CHARACTERISTICS[microgesture] :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{charac}'. " +
                                f"Expected value is one of {list(MICROGESTURE_CHARACTERISTICS[microgesture].keys())}")
            
        result.append(MicrogestureExportSpec(spec, layer, finger, microgesture, charac, element))
        return result
    
    def __str__(self) -> str:
        return f"MicrogestureExportSpec({self.finger}, {self.microgesture}, {self.characteristic})"

    def __repr__(self) -> str:
        return str(self)
    
    
class WristOrientationExportSpec(object):
    """
    A description of how to export a family layer.
    """

    ATTR_ID = "mgrep-wrist-orientation"

    def __init__(self, layer: object, wrist_orientation : str):
        self.layer = layer
        self.wrist_orientation = wrist_orientation

    @staticmethod
    def create_specs(layer, logit=logging.info) -> list:
        """
        Extracts '[finger][status]' from the layer's ATTR_ID attribute 
        and '[wrist_orientation]' from the layer's ELEMENT_ID attribute
        
        Returns either an empty list or a list of FamilyExportSpec element. 
        A RuntimeError is raised if it is incorrectly formatted.
        """
        result = list()

        if WristOrientationExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        wrist_orientation = layer.source.attrib[WristOrientationExportSpec.ATTR_ID]
        
        if wrist_orientation not in WRIST_ORIENTATIONS :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{wrist_orientation}'. " +
                                f"Expected value is one of {list(WRIST_ORIENTATIONS.keys())}")
            
        result.append(WristOrientationExportSpec(layer, wrist_orientation))
        return result
    
    def __str__(self) -> str:
        return f"WristOrientationExportSpec({self.wrist_orientation})"
    def __repr__(self) -> str:
        return str(self)
    
class FingerStatusExportSpec(object):
    """
    A description of how to export a family layer.
    """

    ATTR_ID = "mgrep-finger-poses"

    def __init__(self, layer: object, finger: str, status: str):
        self.layer = layer
        self.finger = finger
        self.status = status

    @staticmethod
    def create_specs(layer, logit=logging.info) -> list:
        """
        Extracts '[finger][status]' from the layer's ATTR_ID attribute 
        and '[wrist_orientation]' from the layer's ELEMENT_ID attribute
        
        Returns either an empty list or a list of FamilyExportSpec element. 
        A RuntimeError is raised if it is incorrectly formatted.
        """
        result = list()
        if FingerStatusExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        spec = layer.source.attrib[FingerStatusExportSpec.ATTR_ID]
        
        g_split = spec.split(",")

        if len(g_split) != 2 :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{spec}'. " +
                                f"Expected value is of the form '[finger][status]'")
        
        finger = g_split[0].replace(" ", "")
        status = g_split[1].replace(" ", "")
        
        if finger not in FINGERS_WITH_THUMB :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{finger}'. " +
                                f"Expected value is one of {list(FINGERS_WITH_THUMB.keys())}")
        if status not in ACCEPTED_STATUSES[finger] :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{status}'. " +
                                f"Expected value is one of {list(ACCEPTED_STATUSES[status].keys())}")
            
        result.append(FingerStatusExportSpec(layer, finger, status))
        return result
    
    def __str__(self) -> str:
        return f"FingerStatusExportSpec({self.finger}, {self.status})"
    def __repr__(self) -> str:
        return str(self)