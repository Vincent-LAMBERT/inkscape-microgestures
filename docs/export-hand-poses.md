
# Inkscape Plugin: Export Hand Poses
Inkscape v1.2.0+ plugin to export the hand poses corresponding to your SVG layers.
This plugin was developed using Nikolai Shkurkin's plugin export-layers-combo (https://github.com/nshkurkin/inkscape-export-layer-combos) as a base. 

## Installation

Download `export_hand_poses.inx` and `export_hand_poses.py`, then copy them to the Inkscape installation folder subdirectory `share\inkscape\extensions`.

- On Windows this may be `C:\Program Files\Inkscape\share\inkscape\extensions` (or `%appdata%\inkscape\extensions` if you don't want to install globally)
- On Ubuntu, this may be `/usr/share/inkscape/extensions/` or (`~/.config/inkscape/extensions` if you don't want to install globally)
- On macOS, this may be `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions`

- Generally, you should be able to go to the Inkscape `Preferences`, select `System`, and see the path for `User extensions`

If the downloaded files have `.txt` suffixes added by GitHub, be sure to remove them. Restart Inkscape if it's running.

## How it works

Open the `Layers` and `XML Editor` tabs. In the `XML Editor` select layer objects and add the attribute `export-hand-poses` to them and given them a value of the form `[finger],[status]`. 

* `[finger]` is the name of the finger the layer corresponds to. 
* `[status]` (one of `up, down, adduction, abd-linkd, complex`) controls the visibility of the layer and how combinations are formed with each finger. `adduction` and `abduction` work in pair to create a link between two joined fingers. `complex` is used to create a link between multiple joined fingers.

You use the tool by running "**Extensions > Export > Export Hand Poses...**". Once you have configured your settings, you hit `Apply` to generate the combinations.

When you export images, the name of the image is of the form `[finger1]-[status1]-[finger2]-[...].png`.

## Working case
We aim to export hand poses from a single SVG file with multiple layers having the following structure.

```
 layer1
    layer1A   -  thumb, up
    layer1B   -  thumb, down
 layer2
    layer2A   -  index, up
    layer2B   -  index, down
    layer2C   -  index, adduction
    layer2D   -  index, complex
 layer3
    layer3A   -  middle, up
    layer3B   -  middle, down
    layer3C   -  middle, adduction
    layer3D   -  middle, abduction
    layer3E   -  middle, complex
 layer4
    layer4A   -  ring, up
    layer4B   -  ring, down
    layer4C   -  ring, adduction
    layer4D   -  ring, abduction
    layer4E   -  ring, complex
 layer5
    layer5A   -  pinky, up
    layer5B   -  pinky, down
    layer5C   -  pinky, abduction
    layer5D   -  pinky, complex
```

When you run the tool, it will generate various hand poses corresponding to your designs. Please make sure your layers overlap correctly as the final results depends on the order of the layers.