<p align="center">
<div style="display: table; margin: 0 auto">
    <h1 style="display: table-cell; vertical-align: middle;padding-right: 20px">microrep</h1>
    <span style="display: table-cell; vertical-align: middle;padding-right: 5px"><img src="./docs/images/microRep_full.png" alt="Project Settings screenshot" height="75" width="75"/></span>
    <span style="display: table-cell; vertical-align: middle;"><img src="./docs/images/python_logo.png" alt="Project Settings screenshot" height="75" width="75"/></span>
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
    General Information - Home Page
</h3>

---


This package is made of 6 subpackages that allows you to batch export and modify representations of microgestures.
You can create a large number of representations and find the designs that best matches your needs or quickly create representations and iterate on them for research purposes. 

Each subpackage can be used in a Command Line Interface (CLI), in Python scripts or even directly in Inkscape (tested with Inkscape v1.2.0, see the [*Inkscape installation steps*](./docs/inkscape-installation-steps.md) :art:).

## Main Concepts 

This package is based on a few main concepts:

* **Microgestures** are quick and subtle finger movements that do not involve the wrist nor the arm. In this package, we focus on three microgestures: *tap*, *swipe* and *hold*.
* **Representations** visually explain how to perform microgestures by showing the moving finger, i.e. the *actuator*, the target, i.e. the *receiver*, and the trajectory of the microgesture. There are two types of representations: 
  * *Single-picture representations of microgestures* describe illustrations that shows one microgesture per hand shape. Multiple single-picture representations are typically used to illustrate a set of microgestures.
  * *Simultaneous representations of microgestures* describe illustrations that shows multiple microgestures on the same hand shape.
* **Families** describe the consistent set of visual cues used to shape the representations of each microgesture. You can use the `mgrep-family-layer` and the `mgrep-path-element` attributes to attribute your own visual cues to the available microgestures.
* **Markers** define the key points of the representations. They are used to define the position of the visual cues defined by the families for the different microgestures. You can use the `mgrep-marker` attribute to define the markers. It accepts a value with the shape `[finger],[microgesture],[characteristic],[markerType]`. `[finger]` can be one of `thumb`, `index`, `middle`, `ring` or `pinky`. `{microgesture]` can be one of `tap`, `swipe` or `hold`. `[characteristic]` can be one of `nail`, `tip` or `middle`, `base`, `up`, `down`, `left`, `right`. `[markerType]` can be one of `actuator`, `receiver`, `traj-start`, `traj-end`.

The file `initial.svg` is an example of a base file that can be used as a starting point (with the `export_hand_poses` :raised_hand: subpackage). If you inspect it, you will find that it is structured and annotated according to these concepts.. For more details, please refer to the detailed documentation of each subpackage

### Documentation for each subpackage

:bookmark_tabs: [**Export Hand Poses**](./docs/export-hand-poses.md) :raised_hand:
&emsp;&ensp; Export different hand poses from a base file (see `initial.svg`).


:bookmark_tabs: [**Create Representations**](./docs/create-representations.md) :cyclone: 
&emsp;&ensp; Create one or multiple representations based on a previously exported hand pose (see the `export_hand_poses` :raised_hand: subpackage).


:bookmark_tabs: [**Map Commands**](./docs/map-commands.md) :game_die: 
&emsp;&ensp; Create one or multiple command mappings for an existing representation of microgestures (see the `create_representations` :cyclone: subpackage).

#### Optional subpackages

This package also includes 3 optional subpackages that were developped for experiment purposes (see [*experiment 1*](./docs/experiment-simultaneous-representations.md) and [*experiment 2*](./docs/experiment-help-interface.md)).

:bookmark_tabs: [**Add Enhancement**](./docs/add-enhancement.md) 
&emsp;&ensp; Create modified versions, of a given representation, e.g. changed colors or shrunken visual cues (optional step after the `create_representations` :cyclone: subpackage).


:bookmark_tabs: [**Add Legend**](./docs/add-legend.md)
&emsp;&ensp; Add a legend to the copy of a given representation (optional step after the `create_representations` :cyclone: subpackage).


:bookmark_tabs: [**Add Overlap Adaptation**](./docs/add-overlap-adaptation.md)
&emsp;&ensp; Modifies the copy of a given representation to make sure the commands do not overlap when working on representations using both the tap and the hold microgestures (optional step after the `create_representations` :cyclone: subpackage).

## Installation

You can install the `microrep` package by simply running `python3 -m pip install microrep` in a terminal. Pip should automatically install the required dependencies. If not, please check the main dependencies of this package with the list below :
- inkex
- lxml
- shapely
- svg.path

If during your installation another module is missing, please check your local distribution before warning us for a missing module in this list.

In case you want to build the module locally, you can run `python3 -m build` in the root folder of the project. This will create a `.tar.gz` file in the `dist` folder that you can install with `python3 -m pip install dist/microrep-{version}.tar.gz`.

## Credits

This `microrep` package was developed using Nikolai Shkurkin's extension export-layers-combo (https://github.com/nshkurkin/inkscape-export-layer-combos) as a base. 

## License

Except for the `cairosvgmg` folder (``tests/experiment_help_interface/cairosvgmg`` and ``tests/test_final_design/cairosvgmg``), which is a copy of the `cairosvg` library, this project is licensed under the MIT License. The `cairosvgmg` folder contains the source code of the `cairosvg` library, which is licensed under the GNU Lesser General Public License v3.0 (LGPL-3.0). You can find its full license text in the `cairosvgmg/LICENSE` file.

The MIT License of this project as a whole can be found at the root folder of the project.