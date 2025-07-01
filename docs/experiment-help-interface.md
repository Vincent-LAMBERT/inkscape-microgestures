<p align="center">
<div style="display: table; margin: 0 auto">
    <h1 style="display: table-cell; vertical-align: middle;padding-right: 20px">microrep</h1>
    <span style="display: table-cell; vertical-align: middle;padding-right: 5px"><img src="./images/microRep_Full.png" alt="Project Settings screenshot" height="75" width="75"/></span>
    <span style="display: table-cell; vertical-align: middle;"><img src="./images/python_logo.png" alt="Project Settings screenshot" height="75" width="75"/></span>
</div>
<h3 align="center">A Python Package to Create Representation of Microgestures</h3>
</p>
<p align="center">
  <p align="center">
    <a href="https://vincent-lambert.eu/">Vincent Lambert</a><sup>1</sup>
    ·
    <a href="http://alixgoguey.fr/">Alix Goguey</a><sup>1</sup>
    ·
    <a href="https://malacria.com/">Sylvain Malacria</a><sup>2</sup>
    ·
    <a href="http://iihm.imag.fr/member/lnigay/">Laurence Nigay</a><sup>1</sup>
    <br>
    <sup>1</sup>Université Grenoble Alpes <sup>2</sup>Université Lille - INRIA
  </p>
</p>

---

<h3 align="center">
    Experiment 2: Designing a Help Interface for Hand Microgestures
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

---

This project has been used to setup the representations used to create the representations of the paper *Designing a Help Interface for Hand Microgestures* being submitted concomitantly with the evaluation of the thesis written by Vincent Lambert.
This documentation file provides an overview of the experiment setup but does not explains the details of the experiment itself. We **strongly** recommend reading the paper for a complete understanding of the following lines.

### Installation

To run this test, you need to install the `cairosvg` module requirements. You can do it by simply installing it with `pip install cairosvg`. We use a modified version of the `cairosvg` library which is contained in the `cairosvgmg` folder and called directly in the `setup_experiment.py` script.

### Usage

Simply run the `setup_experiment.py` script	to create the representations. They will appear in the `output/smartwatch-export` folder under the png format.

### Base file

At the root of this folder, you will find the  `base_right.svg` files. It is the starting point for the different representations of the help interface. During our tests, we played with the left hand which is simply a mirrored version of the base_right file. We commented the related code in the `setup_experiment.py` script if you want to generate representations for the left hand.

### Config files

The configuration files at the root of this project are meant to specify the hand poses of the 3 help interfaces tested in the experiment. You can add or remove hand poses in these folders to note that the script only compute the representations for the specified hand poses. 

The configuration files for the representations of the MimicHandPose and for the command mappings of the 3 help interfaces are computed automatically when running the `setup_experiment.py` script.

### The setup_experiment.py script

This script is used to generate the representations of the help interface for the 3 tested interfaces: MimicHandPose, CommandMapping, and CommandMappingWithHelp. It uses the base files and the configuration files to create the SVG representations of the help interface.

In details, it does the following for each help interface:
1. Create the hand pose files from the `base_right.svg` file according to the corresponding configuration file.
2. Create the representations for the hand poses in the `mimic_hand_pose` folder (deleted in the end of the script).
3. Create the command mapping files for the representations in the corresponding mapping folder (deleted in the end of the script).
4. Convert to PNG the SVG files to be used in the experiment.
5. Copy the PNG files to the `output/smartwatch-export` folder.

### The blank and no_help_available files

Just ignore them. They are necessary to run the experiment on the smartwatch as transition panes and are copied into the output folder by the `get_kotlin_dicts.py` script.

### The get_kotlin_dicts.py script

This script is used to generate the Kotlin dictionaries for the smartwatch application. It reads the PNG files from the `output/smartwatch-export` folder and generates the `copy_to_kotlin.txt`. This file contains the Kotlin dictionaries to copy and paste in the kotlin code of the smartwatch application. 

Finally, to make the smartwatch application usable, you need to import as drawables the PNG files in the `output/smartwatch-export` folder. 

### License
Except for the `cairosvgmg` folder, which is a copy of the `cairosvg` library, this project is licensed under the MIT License. The `cairosvgmg` folder contains the source code of the `cairosvg` library, which is licensed under the GNU Lesser General Public License v3.0 (LGPL-3.0). You can find its full license text in the `cairosvgmg/LICENSE` file.

The MIT License of this project as a whole can be found at the root folder of the project.