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
    Add Enhancement
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_add_enhancement/initial.svg</code> file
</p>

---

This subpackage allows you to add enhancements to representations of microgestures, i.e. change the color or size of its visual cues, given a base SVG and a configuration file. You can either create your own base file, copy our base file or use the result of a previously exported hand pose (see the `create_representations` :cyclone: subpackage).

### Usage

With the `add_enhancement` subpackage, you can use various parameters to control the output :

1. path : The directory to export into
2. filetype : Exported file type. One of [svg|png|jpg|pdf]
3. dpi : DPI of exported image (if applicable)
4. config : Configuration file used
5. debug : Debug mode (verbose logging)

The following sections will explain the structure of the configuration file and the structure of the specific base file, to make sure you can create your own from scratch if you need to.
Make sure to read it with the base file openned to better understand the explanations.

### Specify the enhancement: the configuration file

Each subpackage uses a different kind of configuration file. For the `add_enhancement` subpackage, the configuration file allows to style an existing representation using the following structure for each line : ``"[enhancement name] : ([microgesture], [characteristic], [value])[--([microgesture], [characteristic], [value])]*"``

`tests/test_add_enhancement/config.csv` file:

```csv
    "brightness : (tap, fill, #383838)--(tap, stroke, #383838)--(swipe, fill, #A5A3A3)--(swipe, stroke, #A5A3A3)"
    "size : (swipe, path-scale, 0.5)"
```
