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
    Map Commands &#127922;
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

<p align="center">
    <u>Note:</u> in this documentation page, the base file corresponds to the <code>tests/test_map_commands/initial.svg</code> file
</p>

---

This subpackage allows you to create commands mappings for a given representation of microgestures and a configuration file. This subpackage has been designed to use the result of a representation previously created with the `create_representations` :cyclone: subpackage. You can still create you own base file if you want to but we recommend not to.

### Usage 

With the `map_commands` subpackage, you can use various parameters to control the output :

1. path - The directory to export into
2. filetype - Exported file type. One of [svg|png|jpg|pdf]
3. dpi - DPI of the exported image (if applicable)
4. showMg - Show the microgesture type before the command name, e.g. '[TAP] Stop' instead of 'Stop'
5. radius - Command radius (used to increase only the command icon size without touching the design)
6. prefix - Prefix to add before the exported file name
7. name - Name of the exported file (overrides the prefix if set)
8. config - Configuration file path
9. icons - Icons folder path
10. debug - Debug mode (verbose logging)

The following sections will explain the structure of the configuration file and the structure of the specific base file, to make sure you can create your own from scratch if you need to.
Make sure to read it with the base file openned to better understand the explanations.

### Specify the commands to associate: the configuration file

Each subpackage uses a different kind of configuration file. For the `map_commands` subpackage, the configuration file specifies how  to associate the commands to the visual cues. Each line defines a possible mapping with the following structure: ``finger+microgesture_characteristic-command[,finger+microgesture_characteristic-command]*``.


`tests/test_map_commands/config.csv` file

```csv
  index+tap_tip-dinosaur,index+tap_middle-camel,index+tap_base-cat,index+swipe_up-bat,index+swipe_down-dog
  index+tap_tip-cat,index+tap_middle-camel,index+tap_base-bat,index+swipe_up-dolphin,index+swipe_down-dinosaur
```

You can draw inspiration from the `src/microrep/map_commands/configuration_file.py` file to produce a `config.csv` file corresponding to you own needs if you don't want to do it manually.

### SVG file structure

The base file can contain many elements resulting from the previous subpackages. The `Front` layer can come from the `export_hand_poses` subpackage and the `Family` layer from the `create_representations` subpackage. Nevertheless, the `map_commands` subpackage will only use the `Design` layer.

Base file XML structure:

```xml
  <g inkscape:groupmode="layer" ... inkscape:label="Designs" 
     mgrep-wrist-orientation="front" g>
    <g inkscape:groupmode="layer" ... 
       inkscape:label="AandB_index_swipe_up_trajectory" g>
    <g inkscape:groupmode="layer" ... 
       inkscape:label="AandB_index_swipe_up_actuator" g>
    <g inkscape:groupmode="layer" ... 
       inkscape:label="AandB_index_swipe_up_receiver" g>
    ...
  </g>
```

#### Specify the command placeholder with `mgrep-path-element`

The base file of `create_representations` allows you to create representations while defining the placeholder for each command. To do so, 
you can associate set attribute `mgrep-path-element` of a **circle** to `command`. The `map_commands` subpackage then imports the `icon_placeholder.svg` file and the related icon files, places them onto the placeholders.

### The hidden attributes

To know exactly where the text should be placed, the `map_commands` subpackage uses two hidden attributes:

1. The `mgrep-icon` is an attribute set to `template` in the `icon_placeholder.svg` file to quickly identify the template of the command icon when duplicated. In the SVG files for the icons, the `mgrep-icon` attribute can also be set to `command` for the layer containing the SVG paths and `centroid` to the path used to calculate the centroid of the command icon. 
2. The `mgrep-command` is an attribute set to `template` to identify the whole duplicated template (icon+text) from the `icon_placeholder.svg` file. It can also be set to `text, above`, `text, below`, `text, left` or `text, right` to identify the text layer. Finally, it can also be set to `marker, above`, `marker, below`, `marker, left` or `marker, right` to identify the text markers. Using text markers makes it easier to deal with scaling. 

### Sources

Icons taken from :
Apple, Artichoke, Banana, Baseball, Basketball, Bat, Boot, Bowling, Bowtie, Broccoli, Button, Camel, Cards, Carrot, Cat, Chair, Cherry, Chess, Clock, Coat, Corn, Cucumber, Darts, Dice, Dinosaur, Dog, Dolphin, Pigeon, Pineapple, Plum, Pool, Potato, Printer, Pumkin, Grapes : http://www.svgrepo.com

Duck, Fish, Frog, Tennis, Trash : Icon by <a class="link_pro" href="https://freeicons.io/animal-icons/duck-icon-29564">Fasil</a> on <a href="https://freeicons.io">freeicons.io</a>
Dress sirt, Mouse, Penguin : Icon by <a class="link_pro" href="https://freeicons.io/cloth-icons/clothing-shirt-icon-35835">Raj Dev</a> on <a href="https://freeicons.io">freeicons.io</a>
Enveloppe, Garlic, Lemon, Onion, Peach, Pear, Pepper, Stapler : Icon by <a class="link_pro" href="https://freeicons.io/business-icons/mail-icon-icon">icon king1</a> on <a href="https://freeicons.io">freeicons.io</a>
Gloves : Icon by <a class="link_pro" href="https://freeicons.io/corona/corona-covid-coronavirus-symptom-hand-hands-handwash-gloves-icon-45362">shivani</a> on <a href="https://freeicons.io">freeicons.io</a>
Hat : Icon by <a class="link_pro" href="https://freeicons.io/office-ans-suit/hat-hat-blue-icon-702333">Chatuphoom Nanapo</a> on <a href="https://freeicons.io">freeicons.io</a>
Hockey : Icon by <a class="link_pro" href="https://freeicons.io/betting-icon-set-30632/ice-hockey-exercise-health-competition-wagering-icon-1092099">Iconmarket</a> on <a href="https://freeicons.io">freeicons.io</a>
Karate : Icon by <a class="link_pro" href="https://freeicons.io/japan-icons-set-2/yukata-karate-cultures-kimono-judo-icon-337128">Supalerk laipawat</a> on <a href="https://freeicons.io">freeicons.io</a>
Keyboard : Icon by <a class="link_pro" href="https://freeicons.io/computer-devices-5/keyboard-typing-device-type-icon-861681">Hilmy Abiyyu Asad</a> on <a href="https://freeicons.io">freeicons.io</a>
Mushroom, Socks : Icon by <a class="link_pro" href="https://freeicons.io/autumn-icon-set-7/autumn-mushroom-food-champignon-icon-243503">Satawat Foto Anukul</a> on <a href="https://freeicons.io">freeicons.io</a>
Paperclip : Icon by <a class="link_pro" href="https://freeicons.io/basic-app-icon-set-v.4/clip-document-attachment-paperclip-attach-icon-34575">Mas Dhimas</a> on <a href="https://freeicons.io">freeicons.io</a>
Pencil, Stamp : Icon by <a class="link_pro" href="https://freeicons.io/regular-life-icons/pencil-icon-17870">Anu Rocks</a> on <a href="https://freeicons.io">freeicons.io</a>
Rubiks cube : Icon on <a class="link_pro" href="https://fr.wikipedia.org/wiki/Fichier:Rubiks_cube.svg">Wikipedia</a>
Skirt : Icon by <a class="link_pro" href="https://freeicons.io/clothing-icon-set-4/mini-skirt-clothes-fashion-female-icon-405365">Pongsakorn</a> on <a href="https://freeicons.io">freeicons.io</a>
Strawberry : Icon by <a class="link_pro" href="https://freeicons.io/fruit-and-vegetable-icon-set/strawberry-agriculture-fresh-healthy-food-fruit-bunch-icon-521381">Sorasak Pinwiset</a> on <a href="https://freeicons.io">freeicons.io</a>
Sweater : Icon by <a class="link_pro" href="https://freeicons.io/uniform-icon-set-3/hood-sweatshirt-sweater-clothing-jacket-icon-277075">itim2101</a> on <a href="https://freeicons.io">freeicons.io</a>
Telephone : Icon by <a class="link_pro" href="https://freeicons.io/ui-icons-set/telephone-call-icon-22520">Muhammad Haq</a> on <a href="https://freeicons.io">freeicons.io</a>
T-shirt : Icon by <a class="link_pro" href="https://freeicons.io/e-commerce-and-shopping/fashion-shirt-t-shirt-tshirt-wear-icon-38281">MD Badsha Meah</a> on <a href="https://freeicons.io">freeicons.io</a>
Zebra : <a href="https://www.flaticon.com/free-icons/zebra" title="zebra icons">Zebra icons created by Freepik - Flaticon</a>