# Conversion logic adapted from https://www.hackitu.de/termcolor256/
import math
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QColorDialog, QWidget

# Constants
CURRENT_DIR = Path(__file__).resolve().parent
UI_COLOR_CONVERTER = CURRENT_DIR / "color_converter.ui"
BRIGHTNESS_THRESHOLD = 255 / 2
RGB_SCALE = 95
RGB_SCALE_ADJUST = 55
GRAY_BASE_CODE = 232
GRAY_SCALE_STEP = 10
GRAY_MAX_INDEX = 23
RGB_SCALE_FACTOR = 40
RGB_RED_FACTOR = 36
RGB_GREEN_FACTOR = 6
GRAY_THRESHOLD = 8
FOREGROUND_CODE = 38
BACKGROUND_CODE = 48
ANSI_255_FORMAT = 2
RGB_FORMAT = 5


def to_hex(rgb):
    total = (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]
    hex_str = hex(total)[2:]
    return f"#{hex_str.zfill(6)}"


def lookup_rgb(value, round_mode):
    index = (
        round_mode(value / RGB_SCALE)
        if value < RGB_SCALE
        else round_mode((value - RGB_SCALE_ADJUST) / RGB_SCALE_FACTOR)
    )
    out = 0 if index <= 0 else index * RGB_SCALE_FACTOR + RGB_SCALE_ADJUST
    return index, out


def lookup_gray(value):
    index = 0 if value < GRAY_THRESHOLD else min(round((value - GRAY_THRESHOLD) / GRAY_SCALE_STEP), GRAY_MAX_INDEX)
    code = GRAY_BASE_CODE + index
    out = index * GRAY_SCALE_STEP + GRAY_THRESHOLD
    return code, out


def convert_rgb(rgb_in, round_mode):
    r_index, r_out = lookup_rgb(rgb_in[0], round_mode)
    g_index, g_out = lookup_rgb(rgb_in[1], round_mode)
    b_index, b_out = lookup_rgb(rgb_in[2], round_mode)
    code = (RGB_RED_FACTOR * r_index) + (RGB_GREEN_FACTOR * g_index) + b_index + 16
    return code, [r_out, g_out, b_out]


def convert_gray(rgb_in):
    avg = round((rgb_in[0] * 0.299) + (rgb_in[1] * 0.587) + (rgb_in[2] * 0.114))
    code, out = lookup_gray(avg)
    return code, [out, out, out]


def sqdist(a, b):
    return math.ceil(math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2)))


def to_description(code, rgb_in, rgb_out, color_type):
    ansi255 = f"[{color_type};{ANSI_255_FORMAT};{code!s}m"
    ansirgb = f"[{color_type};{RGB_FORMAT};{rgb_out[0]};{rgb_out[1]};{rgb_out[2]}m"
    return (
        f"Code: {code}<br>"
        f"Hex: {to_hex(rgb_out)}<br>"
        f"Delta: ±{sqdist(rgb_out, rgb_in)}<br>"
        f"ANSI: {ansi255}<br>"
        f"RGB: {ansirgb}"
    )


def convert(value, color_type):
    rgb_in = [int(value[i : i + 2], 16) for i in range(1, 7, 2)]
    gray_code, gray_rgb = convert_gray(rgb_in)
    color_code, color_rgb = convert_rgb(rgb_in, round)
    color_code_floor, color_rgb_floor = convert_rgb(rgb_in, math.floor)
    color_code_ceil, color_rgb_ceil = convert_rgb(rgb_in, math.ceil)
    ansi_rgb = f"[{color_type};{RGB_FORMAT};{rgb_in[0]};{rgb_in[1]};{rgb_in[2]}m"

    return {
        "in_preview": f"{value}",
        "in_ansi_rgb": ansi_rgb,
        "out_gray_preview": to_hex(gray_rgb),
        "out_color_preview": to_hex(color_rgb),
        "out_color_preview_floor": to_hex(color_rgb_floor),
        "out_color_preview_ceil": to_hex(color_rgb_ceil),
        "gray_desc": to_description(gray_code, rgb_in, gray_rgb, color_type),
        "color_desc": to_description(color_code, rgb_in, color_rgb, color_type),
        "floor_desc": to_description(color_code_floor, rgb_in, color_rgb_floor, color_type),
        "ceil_desc": to_description(color_code_ceil, rgb_in, color_rgb_ceil, color_type),
    }


def is_bright(hex_color):
    rgb = [int(hex_color[i : i + 2], 16) for i in range(1, 7, 2)]
    brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return brightness > BRIGHTNESS_THRESHOLD


class ColorConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_COLOR_CONVERTER, self)

        self.color_picker_button.clicked.connect(self.show_color_dialog)
        self.is_foreground.toggled.connect(self.update_color_type)
        self.is_background.toggled.connect(self.update_color_type)

        self.color_type = FOREGROUND_CODE

    def update_color_type(self):
        self.color_type = FOREGROUND_CODE if self.is_foreground.isChecked() else BACKGROUND_CODE
        if hasattr(self, "current_color") and self.current_color:
            self.update_colors(self.current_color)

    def set_color(self, label, hex_color):
        color = QColor(hex_color)
        palette = label.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        palette.setColor(QPalette.ColorRole.WindowText, QColor("black") if is_bright(hex_color) else QColor("white"))
        label.setPalette(palette)
        label.setAutoFillBackground(True)

    def update_colors(self, hex_color):
        result = convert(hex_color, self.color_type)

        self.set_color(self.in_preview, result["in_preview"])
        self.set_color(self.out_gray_preview, result["out_gray_preview"])
        self.set_color(self.out_color_preview, result["out_color_preview"])
        self.set_color(self.out_color_preview_floor, result["out_color_preview_floor"])
        self.set_color(self.out_color_preview_ceil, result["out_color_preview_ceil"])

        self.in_preview.setText(f"HEX: {result['in_preview']}\nRGB: {result['in_ansi_rgb']}")
        self.out_gray_preview.setText(result["gray_desc"])
        self.out_color_preview.setText(result["color_desc"])
        self.out_color_preview_floor.setText(result["floor_desc"])
        self.out_color_preview_ceil.setText(result["ceil_desc"])

    def show_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.update_colors(self.current_color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ColorConverterApp()
    ex.show()
    sys.exit(app.exec())
