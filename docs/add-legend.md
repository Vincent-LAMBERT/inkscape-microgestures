# Inkscape Extension: Add Legend

In the default case, commands are displayed as Icons with nearby labels. However, you could also want to organize those labels in a legend. This extension allows you to add this legend to a simultaneous representation of microgestures. It needs to be used before the map_commands extension.

**Make sure to read the following sections with `example/inital.svg` openned to better understand the explanations.**

## Adding a legend

In case you want to add a legend, you need to specify how you want to regroup the commands. To do so, you can use a config file to define the groups. In the config file, each line defines a possible organization with groups respecting the following structure : ``finger+microgesture-characteristic[_finger+microgesture-characteristic]*``.

Example :

- `example/config.csv` file
    - index+tap-tip_index+swipe-up_index+tap-middle_index+swipe-down_index+tap-base

In this example, all the microgestures are in the same frame. If you want to separate them, you can use the `,` character instead of a `_`.

