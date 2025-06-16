# Inkscape Extension: Create Representations

This submodule allows you to create simultaneous representations of microgestures given a base SVG and a config file.

**Make sure to read the following sections with `example/inital.svg` openned to better understand the explanations.**

## Setup your base SVG document
First, create two separate groups for both **Families** and **Markers** (see the general README.md for the definition of these terms). You can use the `Layers` tab to create them. We highly recommend you to copy the groups from the `example/initial.svg` file to your own SVG file.

Example :

- `example/initial.svg` file
  - `g` : `Families`
    - `g` : `AandB` ...
    - `g` : `MaS` ...	
  - `g` : `Markers`
    - `g` : `Thumb` ...
    - `g` : `Index` ...
    - `g` : `Middle` ...
    - `g` : `Ring` ...
    - `g` : `Pinky` ...

## Describe families

A family is defined by a set of visual cues that will allow to produce representations of microgestures with a consistent design. For example, the `AandB` family uses an Arrow and a Ball to trace the trajectory of the microgestures and emphasize the touched area.

### Declaring a visual cue with `mgrep-family-layer`

Each visual cue has to be child of a group having the `mgrep-family-layer` attribute. These attributes can be seen in the `XML Editor` tab of Inkscape. The `mgrep-family-layer` attribute can take values with the shape `[family],[element]`.

* `[family]` is the name of the family. It can be any string.	
* `[element]` is the type of the element. It can be either `actuator`, `receiver` or `trajectory`.

Within one family, different visual cues could be used. For example a given family could use a straigth line for swipes and a curve for taps. To do so, you would have to create multiple layers and specify the `[microgesture]` as a third parameter. You can also specify one step further with the microgesture `[characteristic]`. Those two parameters are optional.

* `[microgesture]` is the name of the microgesture. It can be either `tap`, `swipe`, `flex`. They can be combined with the `|` character. For example, `tap|swipe` would mean that the layer is used for both the tap and the swipe.
* `[characteristic]` is the name of the characteristic. For the `tap`, it can be either `tip`, `middle` or `base`. For the *swipe* and the *flex*, it can be either `up` or `down`.

Example :

- `example/initial.svg` file
  - `g` : `Families`
    - `g` : `AandB`
      - `g` : `Trajectory` ...
      - `g` : `Receiver`
        - `g` : `Tap` -> `mgrep-family-layer` : `AandB,receiver,tap`
        - `g` : `Hold` -> `mgrep-family-layer` : `AandB,receiver,hold`
      - `g` : `Actuator` ...
    - `g` : `MaS` ...
  - `g` : `Markers` ...

### Specify the visual cue design with `mgrep-path-element`

For each group declaring a visual cue with the attribute `mgrep-family-layer`, you **MUST** define the nature of the group children. You can do so by adding the attribute `mgrep-path-element` to each element and give them one of the following values :
* `design` for the **path** that will be exported as a design. CAUTION : The translation of this design will be based on its centroid which depend on the path's nodes !
* `trace` for the **path** that can be used as a reference for the design path (see `example/initial.svg`).
* `trace-start-bound` and `trace-end-bound` for the **circle** that would be used as to define a zone in which the design points do not scale (see `example/initial.svg`).
* `command` for the **circle** that would be used as a placeholder to later define the command associated to a microgesture.

**CAUTION** : to be valid, a visual cue must have at least one `design` path

Example :

- `example/initial.svg` file
  - `g` : `Families`
    - `g` : `AandB`
      - `g` : `Trajectory` ...
      - `g` : `Receiver`
        - `g` : `Tap`
          - `path` : `Design` -> `mgrep-path-element` : `design`	
          - `circle` : `TraceEndBound` -> `mgrep-path-element` : `trace-end-bound`
          - `circle` : `Command` -> `mgrep-path-element` : `command`
        - `g` : `Hold` ...
      - `g` : `Actuator` ...
    - `g` : `MaS` ...
  - `g` : `Markers` ...

## Export the representations using markers

### Specify key positions with markers having the `mgrep-marker` attribute

Each marker define the position of the visual cues defined by the families for the different microgestures. This is done with the `mgrep-marker` attribute which accepts a value with the shape `[finger],[microgesture],[characteristic],[markerType]`. 

- `[finger]` is the name of the finger. It can be either `thumb`, `index`, `middle`, `ring` or `pinky`.

`[microgesture]` and `[characteristic]` follow the same rules as for the families but the microgesture cannot be combined with the `|` character in this case. 

- `[markerType]` can be either `actuator`, `receiver`, `traj-start`, `traj-end`. It is highly related to the type of the element defined in the family as each type of marker is used to serve as a reference for positionning a specific type of element.

Example :

- `example/initial.svg` file
  - `g` : `Families` ...	
  - `g` : `Markers`
    - `g` : `Thumb` ...
    - `g` : `Index` 
        - `g` : `Swipe`
            - `g` : `SwipeDownTrajEnd` -> `mgrep-marker` : `index,swipe,down,traj-end`
            - `g` : `SwipeDownTrajStart` -> `mgrep-marker` : `index,swipe,down,traj-start`
            - `g` : `SwipeUpTrajEnd` -> `mgrep-marker` : `index,swipe,up,traj-end`
            - `g` : `SwipeUpTrajStart` -> `mgrep-marker` : `index,swipe,up,traj-start`
        - `g` : `Hold` ...
        - `g` : `Tap` ...
        - `g` : `Tap/Hold` ...
    - `g` : `Middle` ...
    - `g` : `Ring` ...
    - `g` : `Pinky` ...

### Specify the combinations of microgestures to export
Once you understand how the extension works and you have your SVG file ready, you can specify the combinations of microgestures you want to export. You can do so by specifying a `.csv` file in the `Configuration file used to export (Optional)` field of the Inkscape window. 

Each row of the file define a combination of microgesture representations to export and should have the following structure : *microgesture1-characteristic1, microgesture2-characteristic2, ...*.

Example :

- `example/config.csv` file
    - *index+tap-tip,index+tap-middle,index+tap-base,index+swipe-up,index+swipe-down*
    - *index+tap-tip,index+tap-middle,index+tap-base,index+hold-tip,index+hold-middle,index+hold-base*

You can modify the `configuration_file.py` file to compute a `.csv` file corresponding to you own needs if you don't want to do it manually.