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
    Inkscape installation steps
</h3>
<p align="center">
    Go back to <a href="../README.md">Home Page</a>
</p>

---

## From a python package to an Inkscape extension

First of all, make sure you change your Inkscape python interpreter to your `python` or `python3` interpreter with the `microrep` package installed (or install it in your Inkscape python interpreter). You can do this by editing the `preferences.xml` file whose location is indicated in `Edit -> Preferences -> System: User Preferences`. Then add the following `python-interpreter="'path/to/your/python'"` after `<group id="extensions"`. 

:warning: Please, note that you have to close all Inkscape instances **before** modifying the `preferences.xml` file, otherwise, its content may be erased on close.

Afterwards, you can simply copy the `src/microrep` folder (without the `__init__.py` folder) in the Inkscape installation folder subdirectory (`share\inkscape\extensions`).

- On Windows this should be `C:\Program Files\Inkscape\share\inkscape\extensions` (or `%appdata%\inkscape\extensions` if you don't want to install globally)
- On Ubuntu, this should be `/usr/share/inkscape/extensions/` or (`~/.config/inkscape/extensions` if you don't want to install globally)
- On macOS, this should be `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions`

Finally, restart Inkscape if it's already running.
You can find all the configured paths in `Edit -> Preferences -> System`.


## Running the extensions from Inkscape
You can use the extensions by running `Extensions > Microgestures > Extension Name...`. Once you have configured your settings, you hit `Apply` to generate the representations. 

:warning: :warning: :warning: The extensions may not work if you have not previously applied the transformations. Please run `Extensions > Modify Path > Apply Transform...` to do so.