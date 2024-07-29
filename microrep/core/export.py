### Export functions ###

import logging
import os
import subprocess
import tempfile
from lxml import etree

from .utils import PNG, SVG, JPG, PDF


#####################################################

def get_svg_name(options, svg) :
    """
    Return the name of the SVG file
    """
    # On windows the path is separated by \ and on linux by /
    if os.name == 'nt':
        svg_name = options.input_file.split("\\")[-1].split(".")[0]
    else :
        svg_name = options.input_file.split("/")[-1].split(".")[0]
    # Correct the behavior depending on wheter its launched from a script or a inkscape gui
    if svg_name.split("_")[0] == "ink" :
        svg_name = svg.name
    return svg_name

def to_export(command) :
    """
    Export command message
    """
    if os.name == "nt":
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p :
            p.wait()
    else :
        with subprocess.Popen(command.encode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p :
            p.wait()

def export(document, label, options, logit=logging.info):
    """
    Export the representation
    """
    if hasattr(options, "prefix") :
        prefix = options.prefix
    else :
        prefix = ""
    output_path = os.path.expanduser(options.path)
    # Remove trailing slash for unix and windows
    if os.name == "nt":
        output_path = output_path.rstrip("\\")
    else :
        output_path = output_path.rstrip("/")
    if not os.path.exists(os.path.join(output_path)):
        logit(f"Creating directory path {output_path} because it does not exist")
        os.makedirs(os.path.join(output_path))

    label=prefix+label

    with CustomNamedTemporaryFile().open(f".{SVG}") as fp_svg :
        if options.filetype!=SVG:
            # logit(f"Writing SVG to temporary location {svg_path}")
            svg_path = fp_svg.name
            export_to_svg(document, svg_path)
            export_to_filetype(options.filetype, svg_path, output_path, label, options, logit)
        else :
            svg_path = os.path.join(output_path, f"{label}.{SVG}")
            export_to_svg(document, svg_path)

def export_to_filetype(filetype, svg_path, output_path, label, options, logit=logging.info):
    """
    Export the SVG to the desired filetype
    """
    functions = { PNG : lambda x,y,z: export_to_png(x, y, z, options, logit),
                  JPG : lambda x,y,z: export_to_jpg(x, y, z, options, logit),
                  PDF : lambda x,y,z: export_to_pdf(x, y, z, options, logit)}
    functions[filetype](svg_path, output_path, label)

def export_to_svg(document, dest,):
    """
    Actually export the layers
    """
    if os.name == "nt":
        # Convert dest to long path to avoid os restrictions
        dest = "\\\\?\\" + os.path.abspath(dest)
    document.write(dest)

def export_to_pdf(svg_path, output_path, label, options, logit=logging.info):
    """
    Export the SVG to PDF
    """
    pdf_path = os.path.join(output_path, f"{label}.{PDF}")
    command = f"inkscape --export-type=\"{PDF}\" -d {options.dpi} --export-filename=\"{pdf_path}\" \"{svg_path}\""
    to_export(command)

def export_to_png(svg_path, output_path, label, options, logit=logging.info):
    """
    Export the SVG to PNG
    """
    png_path = os.path.join(output_path, f"{label}.{PNG}")
    command = f"inkscape --export-type=\"{PNG}\" -d {options.dpi} --export-filename=\"{png_path}\" \"{svg_path}\""
    to_export(command)

def export_to_jpg(svg_path, output_path, label, options, logit=logging.info):
    """
    Convert the PNG to JPEG
    """
    with CustomNamedTemporaryFile().open(f".{PNG}") as png_temp_file :
        command = f"inkscape --export-type=\"{PNG}\" -d {options.dpi} --export-filename=\"{png_temp_file.name}\" \"{svg_path}\""
        jpg_path = os.path.join(output_path, f"{label}.{JPG}")
        command = f"convert \"{png_temp_file.name}\" \"{jpg_path}\""

    to_export(command)
    
def special_deepcopy(document):
    root = document.getroot()
    svg_as_string = etree.tostring(root, pretty_print=True).decode("utf-8")
    new_root = etree.fromstring(svg_as_string)
    return etree.ElementTree(new_root)

######################################################################################################################


class CustomNamedTemporaryFile: 
    """
    MODIFIED FROM : https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file
    This custom implementation is needed because of the following limitation of tempfile.NamedTemporaryFile:
    > Whether the name can be used to open the file a second time, while the named temporary file is still open,
    > varies across platforms (it can be so used on Unix; it cannot on Windows NT or later).
    """
    def __init__(self, mode='wb', suffix="", delete=True):
        self._mode = mode
        self._delete = delete
        self.suffix = suffix

    def __enter__(self):
        # Generate a random temporary file name
        file_name = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())+self.suffix
        # Ensure the file is created
        open(file_name, "x").close()
        # Open the file in the given mode
        self._tempFile = open(file_name, self._mode)
        return self._tempFile

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tempFile.close()
        if self._delete:
            os.remove(self._tempFile.name)

    def open(self, suf):    
        # If OS is Windows, use a the CustomNamedTemporaryFile.
        if os.name == "nt":
            file_name = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())+self.suffix
            # Ensure the file is created
            open(file_name, "x").close()
            # Open the file in the given mode
            self._tempFile = open(file_name, self._mode)
        else : # Otherwise, use the standard NamedTemporaryFile.
            self._tempFile = tempfile.NamedTemporaryFile(suffix=suf)
        return self._tempFile

    def close(self):
        self._tempFile.close()
        if self._delete:
            os.remove(self._tempFile.name)