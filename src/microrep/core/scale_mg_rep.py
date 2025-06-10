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
import svg.path
import math

from .utils import *
from .mg_maths import *

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
    xml.set("cx", str(circle[type][COORDINATES].real))
    xml.set("cy", str(circle[type][COORDINATES].imag))

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
        circles[circleType] = {COORDINATES : convert_to_complex(path_cx, path_cy), CIRCLE_RADIUS : path_r}
        xmls[circleType] = xml

def get_bound_zones(parent_layer) :
    """
    Return the bound_zones relative to the given layer
    """    
    path_xmls={}
    circle_xmls={}
    paths={}
    circles={}
    
    for loop_xml in parent_layer.findall(".//{*}path") :
        for pathType in PATH_BASED_TYPES :
            addPathTypeToDicts(pathType, loop_xml, path_xmls, paths)
            
    for loop_xml in parent_layer.findall(".//{*}circle") :
        for circleType in CIRCLE_BASED_TYPES :
            addCircleTypeToDicts(circleType, loop_xml, circle_xmls, circles)
    
    bound_zones = []
    if TRACE_START_BOUND in circles :
        bound_zones.append(circles[TRACE_START_BOUND])
    if TRACE_END_BOUND in circles :
        bound_zones.append(circles[TRACE_END_BOUND])
    return bound_zones

def is_in_bound_zone(point, bound_zone) :
    """
    Return true if the given point is in the given bound_zone
    """
    point = convert_from_complex(point)
    coords = convert_from_complex(bound_zone[COORDINATES])
    distance = math.dist(point, coords)
    return distance < float(bound_zone[CIRCLE_RADIUS])

def scale_point(point, centroid, scale_factor, logit=logging.info) :
    """
    Scale the given point from the given centroid
    """
    centroid = convert_from_complex(centroid)
    point = convert_from_complex(point)
    new_point = centroid + (point - centroid) * scale_factor
    new_point = convert_to_complex(new_point[0], new_point[1])
    return new_point

def scale_path(path, bound_zones, scale_factor, logit=logging.info) :
    """
    Scale each path point from the distance with the 
    centroid of the given bound_zones they are in. 
    Otherwise, do not scale them 
    """
    parsed_path = svg.path.parse_path(path)
    
    for path_segment in parsed_path :
        segment_dict = {START : path_segment.start, END : path_segment.end}
        if hasattr(path_segment, CONTROL_1):
            segment_dict[CONTROL_1] = path_segment.control1
        if hasattr(path_segment, CONTROL_2):
            segment_dict[CONTROL_2] = path_segment.control2
        if hasattr(path_segment, CIRCLE_RADIUS):
            segment_dict[CIRCLE_RADIUS] = path_segment.radius
        
        for key in segment_dict :
            if key==CIRCLE_RADIUS :
                point = convert_from_complex(segment_dict[key])
                point = point * scale_factor
                point = convert_to_complex(point[0], point[1])
                segment_dict[key] = point
            else :
                for bound_zone in bound_zones :
                    if is_in_bound_zone(segment_dict[key], bound_zone) :
                        segment_dict[key] = scale_point(segment_dict[key], bound_zone[COORDINATES], scale_factor, logit)
                        break
            
            if key == START :
                path_segment.start = segment_dict[key]
            elif key == CONTROL_1 :
                path_segment.control1 = segment_dict[key]
            elif key == CONTROL_2 :
                path_segment.control2 = segment_dict[key]  
            elif key == CIRCLE_RADIUS :
                path_segment.radius = segment_dict[key]
            else :
                path_segment.end = segment_dict[key]
    
    path = parsed_path.d()
    return path