<p align="center">
<div style="display: table; margin: 0 auto">
    <h1 style="display: table-cell; vertical-align: middle;padding-right: 20px">microrep</h1>
    <span style="display: table-cell; vertical-align: middle;padding-right: 5px"><img src="./images/microRep_full.png" alt="Project Settings screenshot" height="75" width="75"/></span>
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
    Add Overlap Adaptation
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_add_overlap_adaptation/initial.svg</code> file
</p>

---

This subpackage allows you to modify a given simultaneous representation of microgestures to adapt the command placement to the given overlap context given a previously exported hand pose (see the `create_representations` :cyclone: subpackage). It has been designed to "hard code" specific cases tested in the related research paper. Thus, it is not as generic as the other subpackages. 

### Usage

With the `add_overlap_adaptation` subpackage, you can use various parameters to control the output :

1. path : The directory to export into
2. filetype : Exported file type. One of [svg|png|jpg|pdf]
3. dpi : DPI of exported image (if applicable)
4. strategy : Non spatial strategy used. One of [default|brightness|text]
5. integration : Labels integrated in a legend or placed by default next to the icon. One of [default|integration]
6. debug : Debug mode (verbose logging)

## Adapting to a specific overlap context

A complete overlap occurs when two repesentations of microgestures are superimposed. In this case, the commands of the first representation are hidden by the second one. This subpackage allows you to sligthly modify the resulting representation to adapt it to the context of a complete overlap.

3 strategies exist (see the `strategy` parameter) :	 
  - **Default** : The combined representation resulting from the superposition of the two representations is altered to create a *special* version (see ``tests/test_experiment_simultaneous_representations/svg_files/SpecialSuperimposition.svg``). For example, the hold placeholder can be moved to the left and the tap placeholder can be moved to the right.
  - **Brightness** : The `add_enhancement` subpackage may make the color of one representation brighter than the other. Following the background/foreground Gestalt principle, representations are thus identifiable regardless of how they are superimposed. Command placeholders are moved under to avoid overlap. The hold placeholder is placed below the tap placeholder. Furthermore, "minicons" are added to make easier to associate a command to the corresponding representation.
  - **Text** : The combined representation resulting from the superposition of the two representations is not modified. However, the command placeholders are moved under to avoid overlap. The hold placeholder is placed below the tap placeholder. Afterwards, the text enhancement marked by a `[MICROGESTURE]` tag would be added by the `map_commands` :game_die: subpackage.

The `integration` parameter allows you to choose whether the labels are integrated in a legend or placed by default next to the icon.
In case you want to add a legend, make sure to use the `add_overlap_adaptation` subpackage before the `map_commands` :game_die: subpackage.