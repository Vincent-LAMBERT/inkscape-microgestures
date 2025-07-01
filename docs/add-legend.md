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
    Add Legend
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_add_legend/initial.svg</code> file
</p>

---

This subpackage allows you to add legends to representations of microgestures given a base SVG and a configuration file. You can either create your own base file, copy our base file or use the result of a previously exported hand pose (see the `create_representations` :cyclone: subpackage).

### Usage

In the default case, commands are displayed as Icons with nearby labels. However, you could also want to organize those labels in a legend. This subpackage allows you to add this legend to a representation of microgestures. It needs to be used before the `map_commands` subpackage.

With the `add_legend` subpackage, you can use various parameters to control the output :

1. path : The directory to export into
2. filetype : Exported file type. One of [svg|png|jpg|pdf]
3. dpi : DPI of exported image (if applicable)
4. config : Configuration file used
5. debug : Debug mode (verbose logging)

The following sections will explain the structure of the configuration file and the structure of the specific base file, to make sure you can create your own from scratch if you need to.
Make sure to read it with the base file openned to better understand the explanations.

### Specify the legend: the configuration file

In case you want to add a legend, you need to specify how you want to regroup the commands. To do so, you can use a configuration file to define the groups. In the configuration file, each line defines a possible organization with groups respecting the following structure : ``finger+microgesture-characteristic[_finger+microgesture-characteristic]*``.

`tests/test_add_legend/config.csv` file:

```csv
    index+tap-tip_index+swipe-up_index+tap-middle_index+swipe-down_index+tap-base
    middle+tap-tip_middle+swipe-up_middle+tap-middle_middle+swipe-down_middle+tap-base
```

In this example, all the microgestures are separated in two frames, one per line.

### The hidden attribute

To know exactly what kind of legend display onto the representation, we use a hidden attribute already set on pre-created legend frames: the `mgrep-legend`. It can be set to `legend` to identify the whole legend and move it or to a ordinal number between `first` and `sixth` to identify the markers where to place the commands.