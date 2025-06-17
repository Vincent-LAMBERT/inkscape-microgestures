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
    Export Hand Poses &#9995;
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_export_hand_poses/initial.svg</code> file
</p>

---

This subpackage allows you to export SVG files with different hand poses from a base SVG and a config file. You can either create your own base file, copy our base file or use the result of a previously exported hand pose (see the `export_hand_poses` :raised_hand: subpackage).

### Usage 

With the `export_hand_poses` subpackage, you can use various parameters to control the output :

1. path - The directory to export into
2. filetype - Exported file type. One of [svg|png|jpg|pdf]
3. config - Configuration file path
4. dpi - DPI of the exported image (if applicable)
5. markers - Show or hide markers on the exported image
6. debug - Debug mode (verbose logging)
7. dry - Do not export (for testing purposes)

The following sections will explain the structure of the configuration file and the structure of the specific base file, to make sure you can create your own from scratch if you need to.
Make sure to read it with the base file openned to better understand the explanations.

### Specify the hand poses to export: the configuration file

Each subpackage uses a different kind of configuration file. For the `export_hand_poses` subpackage, the configuration file allows to create hand poses SVG files using the following structure for each line: ``wristorientation_fingerstatus-fingerstatus-fingerstatus-fingerstatus-fingerstatus``. Each line exports a new hand pose. 

`tests/test_export_hand_poses/config.csv` file:

```csv
  front_up-up-up-up-up
  back_up-up-up-up-up
  front-right_up-up-up-up-up
  front-left_up-up-up-up-up
  right_up-up-up-up-up
  left_up-up-up-up-up
  front_up-up-up-close-close
  front_up-up-close-close-close
  right_up-up-flex-flex-close
  back_up-close-close-close-up
```

You can draw inspiration from the `src/microrep/export_hand_poses/configuration_file.py` file to produce a `config.csv` file corresponding to you own needs if you don't want to do it manually.

### SVG file structure

To export different hand poses from the base file, you simply need to understand the concept of layers in Inkscape. Basically, each layer is a group of elements that can be hidden or shown. If a layer is above another, the elements of the upper layer are drawn on top of the elements of the lower layer. We took advantage of this concept to pre-design the hand poses with finger states and wrist orientations. An hand performing the [sign of the horns](https://en.wikipedia.org/wiki/Sign_of_the_horns) can thus be displayed by hiding and showing the right layers. This is exactly what the `export_hand_poses` subpackage does, according to the configuration file.
When you run the tool, it will generate various hand poses corresponding to your designs. Please make sure your layers overlap correctly as the final results depends on the order of the layers.

#### Declaring the wrist orientation with the attribute `mgrep-wrist-orientation`

Each finger status design is different according to the wrist orientation. Thus, each top layer corresponding to the wrist orientation, e.g. Front or Right, must have the attribute `mgrep-wrist-orientation` set to the corresponding wrist orientation among `front`, `right`, `back`, `left`, `front-right`, `front-left`, `back-right` and `back-left`.

Base file XML structure:

```xml
  <g inkscape:groupmode="layer" ... inkscape:label="Front" 
     mgrep-wrist-orientation="front" g>
   <g inkscape:groupmode="layer" ... inkscape:label="Back"
     mgrep-wrist-orientation="back" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Right"   
     mgrep-wrist-orientation="right" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Left" 
     mgrep-wrist-orientation="left" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Front-Right" 
     mgrep-wrist-orientation="front-right" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Back-Left" 
     mgrep-wrist-orientation="back-left" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Front-Left" 
     mgrep-wrist-orientation="front-left" g>...</g>
   <g inkscape:groupmode="layer" ... inkscape:label="Back-Right" 
     mgrep-wrist-orientation="back-right" g>...</g>
    <!-- used by the create_representations subpackage on the exported hand poses -->
   <g inkscape:groupmode="layer" ... inkscape:label="Families" g>...</g>
```

<u>Note:</u> In the following explanations, we will shorten the ```inkscape:groupmode="layer" ... inkscape:label="..."``` part of the XML structure with the term ```...label="..."```. 

#### Declaring the finger statuses with the attribute `mgrep-finger-poses`

Each finger status must have the `mgrep-finger-poses` attribute and be the child of a layer with the `mgrep-wrist-orientation` attribute. These attributes can be seen in the `XML Editor` tab of Inkscape. The ``mgrep-finger-poses`` attribute takes values with the shape `[finger],[status]`.

* `[finger]` is the name of the finger. It can be either `thumb`, `index`, `middle`, `ring` or `pinky`	
* `[status]` is the status of the finger. It can be either `up`, `close`, `flex`, `abduction`, `adduction` or `complex`

The `abduction` and `adduction` statuses work in pair. When you want to export an hand pose with the `abduction` status set to the middle finger in the configuration file, you need to also apply the `adduction` status to the ring finger.
Similarly, when setting the `complex` status, at least three adjacent finger must be set to `complex` in total.

Base file XML structure:

```xml
  <g ...label="Front" mgrep-wrist-orientation="front" g>
      <g ...label="Index" g>
         <g ...label="IndexDown" mgrep-finger-poses="index,close" g>...</g>
         <g ...label="IndexFlex" mgrep-finger-poses="index,flex" g>...</g>
         <g ...label="IndexUp" mgrep-finger-poses="index,up" g>...</g>
         <g ...label="IndexMiddleSimpleJoint" mgrep-finger-poses="index,adduction" g>...</g>
         <g ...label="IndexMiddleComplexJoint" mgrep-finger-poses="index,complex" g>...</g>
      </g>
      <g ...label="Ring" g>...</g>
      <g ...label="Pinky" g>...</g>
      <g ...label="Middle" g>...</g>
      <g ...label="Thumb" g>...</g>
  </g>
  ...
```