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
    Create Representations &#127744;
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_create_single-picture_representations/initial.svg</code> file
</p>

---

This subpackage allows you to create simultaneous representations of microgestures given a base SVG and a configuration file. You can either create your own base file, copy our base file or use the result of a previously exported hand pose (see the `export_hand_poses` :raised_hand: subpackage).

### Usage 

With the `create_representations` subpackage, you can use various parameters to control the output :

1. path - The directory to export into
2. filetype - Exported file type. One of [svg|png|jpg|pdf]
3. dpi - DPI of exported image (if applicable)
4. config - Configuration file used to create representations
5. family - Selected family. One of [AandB|MaS] for our tests
6. traces - Show the traces (for testing purposes)
7. command - Show command placeholders (for testing purposes)
8. radius - Command expected radius (for slight modifications of readability without modifying the design)
9. one_trajectory_only - Depicts one trajectory at max to avoid cluttering (default: True)
10. four - Stop after processing the four first representations of a family  (for testing purposes)
11. one - Stop after processing one family  (for testing purposes)
12. debug - Debug mode (verbose logging)
13. dry - Don't actually do all of the exports  (for testing purposes)

The following sections will explain the structure of the configuration file and the structure of the specific base file, to make sure you can create your own from scratch if you need to.
Make sure to read it with the base file openned to better understand the explanations.

### Specify the microgestures to create: the configuration file

Each subpackage uses a different kind of configuration file. For the `create_representations` subpackage, the configuration file allows to create simultaneous representation of microgestures (see [Home Page](../README.md)) with the following structure for each line: ``microgesture-characteristic[, microgesture-characteristic]*``. Each line gives a new representation. To create single-picture representations of microgestures, you simply need to specify one ``microgesture-characteristic`` for each line.

`tests/test_create_simultaneous_representations/config.csv` file:

```csv
  index+tap-tip,index+hold-tip
  index+tap-tip,index+tap-middle,index+tap-base,index+swipe-up,index+swipe-down
  index+tap-tip,index+tap-middle,index+tap-base,index+hold-tip,index+hold-middle,index+hold-base
  index+tap-tip,index+tap-middle,index+tap-base,index+swipe-up,index+swipe-down,middle+tap-tip,middle+tap-middle,middle+tap-base,middle+swipe-up,middle+swipe-down
```

You can draw inspiration from the `src/microrep/create_representations/configuration_file.py` file to produce a `config.csv` file corresponding to you own needs if you don't want to do it manually.

### SVG file structure

To create representations of microgestures, you need to concepts: **Families** and **Markers** (see the [Home Page](../README.md) for the definition of these terms). We thus used the `Layers` tab in Inkscape to create layers in the base file that contain the elements related to each of these concepts.

Base file XML structure:

```xml
  <g inkscape:groupmode="layer" ... inkscape:label="Families" g>
    <g inkscape:groupmode="layer" ... inkscape:label="AandB" g>...</g>
    <g inkscape:groupmode="layer" ... inkscape:label="MaS" g>...</g>
    ...
  </g>
  <g inkscape:groupmode="layer" ... inkscape:label="Markers" g>
    <g inkscape:groupmode="layer" ... inkscape:label="Thumb" g>...</g>
    <g inkscape:groupmode="layer" ... inkscape:label="Index" g>...</g>
    <g inkscape:groupmode="layer" ... inkscape:label="Middle" g>...</g>
    <g inkscape:groupmode="layer" ... inkscape:label="Ring" g>...</g>
    <g inkscape:groupmode="layer" ... inkscape:label="Pinky" g>...</g>
  </g>
```

<u>Note:</u> In the following explanations, we will shorten the ```inkscape:groupmode="layer" ... inkscape:label="..."``` part of the XML structure with the term ```...label="..."```. 
<u>Note bis:</u> in the base file, the `Markers` layer is named `Front` because it is produced from the `Front` layer of the `export_hand_pose` subpackage (see the [related documentation](export-hand-poses.md) for more details). 

### Describe families

A family is defined by a set of visual cues that will allow to produce representations of microgestures with a consistent design.
In this subpackage, we only included two families: the `AandB` family and the `MaS` family. The first uses an Arrow and a Ball to trace the trajectory of the microgestures and emphasize the touched area. The second uses full and empty geometric shapes, e.g. a disk and a ring, to emphasize the which fingers should come into contact and how.
One family traces the trajectory of context-switching microgestures, the other does not.

#### Declaring a microgesture visual cue with the attribute `mgrep-family-layer`

Each visual cue has to be child of a layer having the `mgrep-family-layer` attribute. These attributes can be seen in the `XML Editor` tab of Inkscape. The `mgrep-family-layer` attribute takes values with the shape `[family],[element]`.

* `[family]` is the name of the family. It can be any string.	
* `[element]` is the type of the element. It can be either `actuator`, `receiver` or `trajectory`.

Within one family, different visual cues can be used. For example a given family can use a straigth line for swipes and a curve for taps. To do so, we create multiple layers and specify the `[microgesture]` as a third parameter. We can also specify one step further with the microgesture `[characteristic]`. Those two parameters are optional.

* `[microgesture]` is the name of the microgesture. It can be either `tap`, `swipe`, `flex`. They can be combined with the `|` character. For example, `tap|swipe` would mean that the layer is used for both the tap and the swipe.
* `[characteristic]` is the name of the characteristic. For the `tap`, it can be either `tip`, `middle` or `base`. For the *swipe*, it can be either `up` or `down`.

`MaS` family layer XML structure:

```xml
  <g ...label="MaS" g>
    <g ...label="Trajectory" g>
      <g ...label="Swipe" mgrep-family-layer="MaS, trajectory, swipe" g>...</g>
    </g>
    <g ...label="Actuator" g>
      <g ...label="Tap/Swipe" mgrep-family-layer="MaS, actuator, tap|swipe" g>...</g>
      <g ...label="Hold" mgrep-family-layer="MaS, actuator, hold" g>...</g>
    </g>
    <g ...label="Receiver" g>
      <g ...label="Tap" mgrep-family-layer="MaS, receiver, tap" g>...</g>
      <g ...label="Hold" mgrep-family-layer="MaS, receiver, hold" g>...</g>
    </g>
  </g>
```

<u>Note:</u> No family currently uses the `[characteristic]` parameter but we considered it necessary while developing the package for including other microgestures in the future or for making it easier for users to create their own families.

#### Specify the visual cue design with `mgrep-path-element`

Each visual cue needs at least a design element. Nevertheless, each microgesture could later be associated with a command and some visual cues may need to be correctly moved and stretched without altering the design. Hence, we created the attribute `mgrep-path-element` that can be used to describe the nature of each child of a layer with the `mgrep-family-layer` attribute :
* `design` for the **path** that will be exported as a design. :warning: The translation of this design will be based on its centroid which depend on the path's nodes !
* `multi-design` for the **path** that will be exported as a design for bi-directional microgestures, e.g. up AND down swipes. :warning: This specific design category is intended to be used with a trace as a reference !
* `trace` for the **path** that will be used as a reference for the design path. If a trace exists, its end points will be translated to the microgesture markers instead of the design itself. Then, the design will be scaled according to how the trace is placed on the design in the definition of the family. It is particularly interesting for the design of the *swipe* microgesture.
* `trace-start-bound` and `trace-end-bound` for the **circle** that will be used as to define a zone in which the design points do not scale when using a trace. :warning: cannot be used without a trace.
* `command` for the **circle** that will be used as a placeholder to later define the command associated to a microgesture (see the `map_commands` :game_die: subpackage).

:warning: To be valid, each visual cue declared with the attribute `mgrep-family-layer` **MUST** have a layer with the `mgrep-path-element` attribute set to `design`! 

`MaS` swipe trajectory layer XML structure:

```xml
  <g ...label="Swipe" mgrep-family-layer="MaS, trajectory, swipe" g>...</g>
    <!-- used when representing only one swipe on a finger --> 
    <g mgrep-path-element="design" g>...</g> 
    <!-- used when representing bi-directional swipes on one finger -->
    <g mgrep-path-element="multi-design" g>...</g>
    <g mgrep-path-element="trace" g>...</g>
    <g mgrep-path-element="trace-start-bound" g>...</g>
    <g mgrep-path-element="trace-end-bound" g>...</g>
    <g mgrep-path-element="command" g>...</g>
  </g>
```

### Export the representations using markers

#### Specify key positions with markers having the `mgrep-marker` attribute

Each marker define the position of the visual cues defined by the families for the different microgestures. This is done with the `mgrep-marker` attribute which accepts a value with the shape `[finger],[microgesture],[characteristic],[markerType]`. 

- `[finger]` is the name of the finger. It can be either `thumb`, `index`, `middle`, `ring` or `pinky`.

`[microgesture]` and `[characteristic]` follow the same rules as for the families but the microgesture cannot be combined with the `|` character in this case. 

- `[markerType]` can be either `actuator`, `receiver`, `traj-start`, `traj-end`. It is highly related to the type of the element defined in the family as each type of marker is used to serve as a reference for positionning a specific type of element.

Base file XML structure:

```xml
  <g ...label="Index" g>...
    <g ...label="Swipe" g>
      <g ...label="SwipeDownTrajEnd" mgrep-marker="index,swipe,down,traj-end" g>...</g>
      <g ...label="SwipeDownTrajStart" mgrep-marker="index,swipe,down,traj-start" g>...</g>
      <g ...label="SwipeUpTrajEnd" mgrep-marker="index,swipe,up,traj-end" g>...</g>
      <g ...label="SwipeUpTrajStart" mgrep-marker="index,swipe,up,traj-start" g>...</g>
    </g>
    <g ...label="Hold" g>...</g>
    <g ...label="Tap" g>...</g>
    <g ...label="Tap/Hold" g>...</g>
  </g>
```

Note: The `Index` layer corresponds to the `Front/Index/IndexUp/Markers` layer in the base file because it is produced from the `Front` layer of the `export_hand_pose` subpackage (see the [related documentation](export-hand-poses.md) for more details).