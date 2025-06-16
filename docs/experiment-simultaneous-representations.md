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

This github projects has been used to setup the representations used in Experiment 1 of the paper *Studying the Simultaneous Visual Representation of Microgestures*

### Installation

No additional installation is required

### Usage

Simply run the `setup_experiment.py` script	to create the representations. They will appear in the `output/mappings` folder under the svg format.

### Code organization

This overview of the code organization is not supposed to be exhaustive and requires a deep understanding of the project. Please refer to the [paper] (https://dl.acm.org/doi/10.1145/3676523) for more details.

The code of this project is divided in 7 steps repeated for the representations with 1 or 2 fingers used, i.e. index finger or index and middle fingers.

- Computing Superimposition and Juxtaposition for the partial occlusion condition (TS condition)
- Computing Superimposition and Juxtaposition for the complete occlusion condition (TH condition)
- Duplicating the default representation to be the base for a text diversification (the text diversification does not modify the design of visual cues and thus the related files are not created by the `add_enhancement` subpackage)
- Adapt the default superimposition representations to be special (we have a `SpecialSuperimposition` file because for specific reasons in this research we want to change the design of the family in very specific cases)
- Adding the legend to the representations
- Compute the adaptations (the adapations allow to correctly map the commands for specific cases of complete occlusion)
- Map the commands

Every subpackage of the `microrep` package his used in this experiment except the `export_hand_poses` subpackage.