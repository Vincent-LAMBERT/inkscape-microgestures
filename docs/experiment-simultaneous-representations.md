<p align="center">
<h1 align="center">Microrep</h1>
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
    Experiment 1: Studying the Simultaneous Visual Representation of Microgestures
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

---

This project has been used to setup the representations used in Experiment 1 of the paper [*Studying the Simultaneous Visual Representation of Microgestures*](https://dl.acm.org/doi/10.1145/3676523).
This documentation file provides an overview of the experiment setup but does not explains the details of the experiment itself. We **strongly** recommend reading the paper for a complete understanding of the following lines.

### Installation

No additional installation is required

### Usage

Simply run the `setup_experiment.py` script	to create the representations. They will appear in the `output/mappings` folder under the svg format.

### Base file

You will find 3 files in the `svg_files` folder: `Superimposition.svg`, `Juxtaposition.svg` and `SpecialSuperimposition.svg`.
There are the starting points for the different representations compared in our experiment. The `SpecialSuperimposition.svg` file is a special case of `Superimposition.svg` in which the we change the design of the family. It is used to replace the representations produced from `Superimposition.svg` but only for the Default Superimposition representations in the TH condition. It gives 4 representations depending on 2 variables: with or without legend and for the A&B or the MaS family.

### Config files

The configuration files in the `configurations` folder are meant to specify the representations to create from the base svg files (`base_*` config files), add enhancements (`style_*` config files), add legends (`legend_*` config files) and create multiple mappings for each representation (`mapping_*` config files). We separated them according to the condition (TS or TH) and the number of fingers involved (1 or 2) to make things clearer.

### The setup_experiment.py script

The script of this project is divided in 7 steps repeated for the representations involving 1 or 2 fingers, i.e. index finger or index and middle fingers.

1. Computing Superimposition and Juxtaposition for the partial occlusion condition (TS condition)
2. Computing Superimposition and Juxtaposition for the complete occlusion condition (TH condition)
3. Duplicating the default representation to be the base for a text diversification (the text diversification does not modify the design of visual cues and thus the related files are not created by the `add_enhancement` subpackage)
4. Adapt the default superimposition representations to be special (we have a `SpecialSuperimposition` file because in this experiment we want to change the design of the family only for the Default Superimposition representations in the TH condition)
5. Adding the legend to the representations
6. Compute the adaptations (the adapations allow to correctly map the commands for specific cases of complete occlusion)
7. Map the commands

Every subpackage of the `microrep` package his used in this experiment except the `export_hand_poses` subpackage.