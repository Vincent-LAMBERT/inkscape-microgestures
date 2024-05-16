# Inkscape Extension: Complete Occlusion Adaptation

This extension allows you to modify a given simultaneous representation of microgestures to adapt the command placement to the given complete occlusion context. It has been designed to "hard code" specific cases tested in the related research paper. Thus, it is not as generic as the other extensions.

**Make sure to read the following sections with `example/inital.svg` openned to better understand the explanations.**

## Adapting to a complete occlusion context

A complete occlusion occurs when two repesentations of microgestures are superimposed. In this case, the commands of the first representation are hidden by the second one. This extension allows you to sligthly change the resulting representation in order to adapt to the complete occlusion context. 

3 cases exist : 
  - **Default** : The combined representation resulting from the superposition of the two representations is altered to create a "merged" version. The hold placeholderis moved to the left and the tap placeholder is moved to the right.
   
  - **Brightness** : The `add_enhancement` extension may make the color of one representation brighter than the other. Following the background/foreground Gestalt principle, representations are thus identifiable regardless of how they are superimposed. Command placeholders are moved under to avoid overlapping. The hold placeholder is placed below the tap placeholder. Furthermore, "minicons" are added to make easier to associate a command to the corresponding representation.
  - **Text** : The combined representation resulting from the superposition of the two representations is not modified. However, the command placeholders are moved under to avoid overlapping. The hold placeholder is placed below the tap placeholder. Afterwards, the text enhancement marked by a `[MICROGESTURE]` tag would be added by the `map_commands` extension.

In case you want to add a legend, make sure to use the `complete_occlusion_adaptation` extension before the `map_commands` extension.

**CAUTION : In opposition with the other extensions, this one is applied directly on the file and is not exported as a new file. It is therefore recommended to backsave your file before using this extension.**