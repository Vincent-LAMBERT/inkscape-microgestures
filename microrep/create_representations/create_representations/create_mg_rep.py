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

import svg.path
import logging

import microrep.core.utils as u
import microrep.core.mg_maths as mg
 
def create_mg_rep(family_layer, element, markers, logit=logging.info) :
    """
    Creates the family representation 
    by moving elements of the family layer
    to the markers positions
    
    family_layer is a dictionnary of the form 
        {element : layer, ...} 
    markers_positions is a dictionnary of the form
        {marker_type : position, ...}
    """
    # Call the moving function depending on the element type
    if u.ELEMENT_SVG_TYPE_CORRESPONDANCE[element] == u.PUNCTUAL :
        if element in markers :
            # In this case, element == markerType as they are both either actuator or receiver
            move_element(family_layer, markers[element][1], logit)
    else :
        move_path(family_layer, markers[u.TRAJ_START][1], markers[u.TRAJ_END][1], logit)

def move_element(parent_layer, position, logit=logging.info) :
    """
    Moves the circle in the parent layer to the given positions
    """
    design_xml = None
    circle_xmls={}
    circles={}
    
    for loop_xml in parent_layer.findall(".//{*}path") :
        if loop_xml.get("mgrep-path-element") == u.DESIGN :
            design_xml = loop_xml
            
    for loop_xml in parent_layer.findall(".//{*}circle") :
        for circleType in u.CIRCLE_BASED_TYPES :
            addCircleTypeToDicts(circleType, loop_xml, circle_xmls, circles)
        
    if design_xml is not None :
        design_path = svg.path.parse_path(design_xml.get("d"))
        design_path = mg.compute_translation(design_xml, position, logit)
        design_xml.set("d", design_path.d())
        
        for command_xml in circle_xmls.values() :
            command_path = mg.compute_translation(command_xml, position, logit)
            command_path_cx = command_path[0].end.real
            command_path_cy = command_path[0].end.imag
            command_xml.set("cx", str(command_path_cx))
            command_xml.set("cy", str(command_path_cy))

def addPathTypeToDicts(pathType, xml, xmls, paths) :
    """
    Adds the parsed path to the paths 
    dictionnary if it is of the given type
    """
    if xml.get("mgrep-path-element") == pathType :
        xmls[pathType] = xml
        path = svg.path.parse_path(xml.get("d"))
        paths[pathType] = path

def setXmlValueFromPathType(type, xml, paths, logit=logging.info) :
    """
    Sets the xml value from the path
    """
    xml.set("d", paths[type].d())

def setXmlValueFromCircleType(type, xml, circle, logit=logging.info) :
    """
    Sets the xml value from the circle
    """
    xml.set("cx", str(circle[type][u.COORDINATES].real))
    xml.set("cy", str(circle[type][u.COORDINATES].imag))

def addCircleTypeToDicts(circleType, xml, xmls, circles) :
    """
    Adds the circle to the paths 
    dictionnary if it is of the given type
    CAUTION : As we want to move its centroid, it
    would be considered as a path with one coordinates
    """
    if xml.get("mgrep-path-element") == circleType :
        path_cx = xml.get("cx")
        path_cy = xml.get("cy")
        path_r = xml.get("r")
        circles[circleType] = {u.COORDINATES : mg.convert_to_complex(path_cx, path_cy), u.CIRCLE_RADIUS : path_r}
        xmls[circleType] = xml

def move_path(parent_layer, start_position, end_position, logit=logging.info) :
    """
    Moves the path in the parent layer to the given positions
    
    CAUTION : In Inkscape, the *End* of the path corresponds here
    to the ending segment and not the first *MoveTo* segment. 
    The path is thus reversed from the documentation 
    here https://www.w3.org/TR/SVG/paths.html
    """    
    path_xmls={}
    circle_xmls={}
    paths={}
    circles={}
    
    for loop_xml in parent_layer.findall(".//{*}path") :
        for pathType in u.PATH_BASED_TYPES :
            addPathTypeToDicts(pathType, loop_xml, path_xmls, paths)
            
    for loop_xml in parent_layer.findall(".//{*}circle") :
        for circleType in u.CIRCLE_BASED_TYPES :
            addCircleTypeToDicts(circleType, loop_xml, circle_xmls, circles)
    
    # If at least one design element if specified
    if u.DESIGN in paths and paths[u.DESIGN] is not None :
        # Compute the new path vector from start to end
        reference_vector = mg.vector(start_position, end_position)
        
        if u.TRACE in paths and paths[u.TRACE] is not None :
            paths, circles = mg.compute_transformation(paths, circles, reference_vector, start_position, paths[u.TRACE], logit)
        else :
            paths, circles = mg.compute_transformation(paths, circles, reference_vector, start_position, False, logit)

        for pathType in path_xmls :
            setXmlValueFromPathType(pathType, path_xmls[pathType], paths, logit)
        for circleType in circle_xmls :
            setXmlValueFromCircleType(circleType, circle_xmls[circleType], circles, logit)