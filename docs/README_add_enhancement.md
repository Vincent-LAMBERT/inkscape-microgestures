# Inkscape Extension: Add Enhancement

This extension allows you to add visual enhancements to a simultaneous representation of microgestures given a config file.

**Make sure to read the following sections with `example/inital.svg` openned to better understand the explanations.**

## Adding a visual enhancement

You may want to enhance an existing representation by slightly modifying its design. To do so, you can use a config file to define modification to apply to the `style` attribute. You also need to specify the microgesture type considered for the enhancement. The modification will be applied to all the visual cues associated to the microgesture type.

Each line of the config file must have the following shape :

`"[enhancement name] : ([microgesture], [characteristic], [value])--([microgesture], [characteristic], [value])--..."`

Example :

- `example/config.csv` file
    - *"color : (tap, fill, #383838)--(tap, stroke, #383838)--(swipe, fill, #A5A5A5)--(swipe, stroke, #A5A5A5)"*
    - *"size : (swipe, path-scale, 0.5)"*
