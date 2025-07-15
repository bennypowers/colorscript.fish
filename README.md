# 🌈 colorscript.fish 🐠 

https://github.com/user-attachments/assets/437e33da-32ba-4328-acf0-2980393cab1a

A modern, Fish-native version of the classic `colorscript` utility, inspired by the [Bash version by DistroTube (DT)](https://gitlab.com/dwt1/shell-color-scripts). This version is packaged as a [Fisher](https://github.com/jorgebucaran/fisher) plugin for simple installation and management of shell color scripts.

## Installation

Install with [Fisher](https://github.com/jorgebucaran/fisher):

```fish
fisher install bennypowers/colorscript.fish
```

## Usage

The main command is `colorscript`.

```
Usage: colorscript [option]
Options:
    -h, --help                Show this help message
    -l, --list                List all color scripts
    -r, --random              Run a random color script
    -e, --exec                Execute a specific color script by name
    --animate <name>          Animate a sequence of colorscripts
        [-d|--delay <ms>]     Delay between frames in milliseconds (default: 333)
    generate <path_or_url>    Generate new colorscripts from a sprite sheet
```

### Examples

- **Run a random script:** `colorscript -r`
- **List all available scripts:** `colorscript -l`
- **Execute a specific script:** `colorscript -e myscript`

### Animating Scripts

The `--animate` option runs a sequence of scripts in a loop. To create an animation, you must name your files according to a specific pattern:

-   `animation_name.fish` (or `.sh`)
-   `animation_name.1.fish`
-   `animation_name.2.fish`
-   ...and so on.

The command `colorscript --animate animation_name` will find all scripts starting with `animation_name` followed by an optional number, sort them naturally, and play them in a loop.

- **Animate a set of scripts:** `colorscript --animate animation_name`
- **Animate with a custom delay:** `colorscript --animate animation_name --delay 100`

## Generating New Scripts

The `generate` subcommand uses a powerful Python script (`gen-colorscript.py`) to create new colorscripts from local or remote sprite sheets. The generator intelligently separates sprites from a sheet, even those with disconnected parts, and prompts you to name and save each one.

To generate scripts:

```fish
colorscript generate /path/to/your/sprites.png
```

Or from a URL:

```fish
colorscript generate https://example.com/sprites.png
```

### Dependencies for the `generate` subcommand:

- **Python 3.6+**
- **Python Libraries**: `Pillow` and `requests`. You can install them using pip:
  ```sh
  pip install Pillow requests
  ```

## Script Directory

Color scripts are stored in the following directory, following the XDG Base Directory Specification:

-   `$XDG_DATA_HOME/colorscripts` (if `$XDG_DATA_HOME` is set)
-   `~/.local/share/colorscripts` (as a fallback)

The `gen-colorscript.py` script will automatically create this directory and save new scripts there.
