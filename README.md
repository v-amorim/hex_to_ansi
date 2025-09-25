## PyQt6 Hex to ANSI

A simple Hex Color to ANSI Code equivalent color, written in Python using PyQt6.

<p align="center">
  <img alt="demo" src="assets/demo.gif" width="100%"/>
</p>

### Features

- Color Picker
- Closest ANSI code to the selected color
  - Code in the '5' pattern, the 256 ANSI
  - Code in the '2' pattern, the RGB ANSI
- Closest Dark and Light color to the selected color
- Closest Grayscale color to the selected color
- Modifiers for the selected color
  - Color modifiers:
    - Foreground
    - Background
  - Text modifiers:
    - Bold
    - Dim
    - Italic
    - Underline
    - Blinking
    - Inverse
    - Invisible/Hidden
    - Strikethrough

### Screenshots

| GUI in its initial state  | Color Picker                            |
| ------------------------- | --------------------------------------- |
| ![default_gui]            | ![color_picker]                         |
| GUI with a color selected | GUI with a color selected and modifiers |
| ![color_selected]         | ![color_modifiers]                      |

<sup>The logic behind the conversion is based on the one used [here][credits].</sup>

### Setup

Install [uv][uv]:

```bash
pip install uv
```

Run the app:

```bash
uv run hex_to_ansi.pyw
```

<!-- URLS -->

[credits]: https://www.hackitu.de/termcolor256/
[uv]: https://docs.astral.sh/uv/getting-started/installation/#pypi
[default_gui]: https://github.com/user-attachments/assets/5a06f9d3-8d70-4ee4-ba37-1ae4fc7ee4f7
[color_picker]: https://github.com/user-attachments/assets/146b9839-6f00-4ca1-9275-481b4cdfbd61
[color_selected]: https://github.com/user-attachments/assets/4a72ed36-bf50-4d8c-b3af-be284a857cec
[color_modifiers]: https://github.com/user-attachments/assets/a8ee7908-08a7-427d-abb3-d5da52cc72c7
