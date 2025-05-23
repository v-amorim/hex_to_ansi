# Conversion logic adapted from https://www.hackitu.de/termcolor256/
import math
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QColorDialog, QWidget

# Constants
UI_CONSTANTS = {
    "CURRENT_DIR": Path(__file__).resolve().parent,
    "BRIGHTNESS_THRESHOLD": 255 / 2,
    "GRAY_BASE_CODE": 232,
    "GRAY_MAX_INDEX": 23,
    "GRAY_SCALE_STEP": 10,
    "GRAY_THRESHOLD": 8,
    "RGB_SCALE": 95,
    "RGB_SCALE_ADJUST": 55,
    "RGB_SCALE_FACTOR": 40,
    "RGB_RED_FACTOR": 36,
    "RGB_GREEN_FACTOR": 6,
    "FOREGROUND_CODE": 38,
    "BACKGROUND_CODE": 48,
    "ANSI_256_FORMAT": 5,
    "RGB_FORMAT": 2,
}

MODIFIER_CODES = {
    "is_bold": "1",
    "is_dim": "2",
    "is_italic": "3",
    "is_underline": "4",
    "is_blinking": "5",
    "is_inverse": "7",
    "is_invisible": "8",
    "is_strikethrough": "9",
}

ColorComponents = tuple[int, int, int]
ColorConversionResult = tuple[int, ColorComponents]


def get_selected_modifiers(widget: QWidget) -> list[str]:
    """Return list of modifier codes for checked modifier checkboxes."""
    return [code for attr, code in MODIFIER_CODES.items() if getattr(widget, attr).isChecked()]


def rgb_to_hex(rgb: ColorComponents) -> str:
    """Convert RGB tuple to hexadecimal color string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()


def calculate_color_distance(color1: ColorComponents, color2: ColorComponents) -> int:
    """Calculate Euclidean distance between two RGB colors."""
    return math.ceil(math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2, strict=True))))


def find_closest_rgb_index(value: int, rounding_func) -> tuple[int, int]:
    """Find closest RGB index and corresponding value for a color component."""
    if value < UI_CONSTANTS["RGB_SCALE"]:
        index = rounding_func(value / UI_CONSTANTS["RGB_SCALE"])
    else:
        index = rounding_func((value - UI_CONSTANTS["RGB_SCALE_ADJUST"]) / UI_CONSTANTS["RGB_SCALE_FACTOR"])

    index = max(0, index)
    output = index * UI_CONSTANTS["RGB_SCALE_FACTOR"] + UI_CONSTANTS["RGB_SCALE_ADJUST"]
    return index, output


def find_closest_gray_index(value: int) -> tuple[int, int]:
    """Find closest gray index and corresponding value for a brightness level."""
    if value < UI_CONSTANTS["GRAY_THRESHOLD"]:
        return UI_CONSTANTS["GRAY_BASE_CODE"], 0

    index = min(
        round((value - UI_CONSTANTS["GRAY_THRESHOLD"]) / UI_CONSTANTS["GRAY_SCALE_STEP"]),
        UI_CONSTANTS["GRAY_MAX_INDEX"],
    )
    code = UI_CONSTANTS["GRAY_BASE_CODE"] + index
    output = index * UI_CONSTANTS["GRAY_SCALE_STEP"] + UI_CONSTANTS["GRAY_THRESHOLD"]
    return code, output


def convert_to_rgb_color(rgb: ColorComponents, rounding_func) -> ColorConversionResult:
    """Convert RGB color to closest ANSI 256-color code using specified rounding method."""
    r_idx, r_val = find_closest_rgb_index(rgb[0], rounding_func)
    g_idx, g_val = find_closest_rgb_index(rgb[1], rounding_func)
    b_idx, b_val = find_closest_rgb_index(rgb[2], rounding_func)

    code = UI_CONSTANTS["RGB_RED_FACTOR"] * r_idx + UI_CONSTANTS["RGB_GREEN_FACTOR"] * g_idx + b_idx + 16
    return code, (r_val, g_val, b_val)


def convert_to_gray_color(rgb: ColorComponents) -> ColorConversionResult:
    """Convert RGB color to closest ANSI gray-scale code."""
    brightness = round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    code, gray_value = find_closest_gray_index(brightness)
    return code, (gray_value, gray_value, gray_value)


def create_ansi_escape_code(color_type: int, color_code: int, modifiers: list[str], rgb: ColorComponents = None) -> str:
    """Create ANSI escape code string for given parameters."""
    parts = [str(color_type)]

    if rgb:
        parts.extend([str(UI_CONSTANTS["RGB_FORMAT"]), *map(str, rgb)])
    else:
        parts.extend([str(UI_CONSTANTS["ANSI_256_FORMAT"]), str(color_code)])

    if modifiers:
        parts.extend(modifiers)

    return f"{';'.join(parts)}m"


def format_color_description(
    ansi_code: int, original_rgb: ColorComponents, converted_rgb: ColorComponents, color_type: int, modifiers: list[str]
) -> str:
    """Create HTML formatted description for color conversion results."""
    ansi_256 = create_ansi_escape_code(color_type, ansi_code, modifiers)
    ansi_rgb = create_ansi_escape_code(color_type, 0, modifiers, rgb=converted_rgb)

    return (
        f"Code: {ansi_code}<br>"
        f"Hex: {rgb_to_hex(converted_rgb)}<br>"
        f"Delta: ±{calculate_color_distance(original_rgb, converted_rgb)}<br>"
        f"256: {ansi_256}<br>"
        f"RGB: {ansi_rgb}"
    )


def convert_hex_color(hex_color: str, color_type: int, modifiers: list[str]) -> dict:
    """Handle all color transformations for the main conversion function."""
    original_rgb = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    input_ansi_rgb = create_ansi_escape_code(color_type, 0, modifiers, rgb=original_rgb)

    # Gray scale conversion
    gray_code, gray_rgb = convert_to_gray_color(original_rgb)

    # Color cube conversions
    color_code, color_rgb = convert_to_rgb_color(original_rgb, round)
    floor_code, floor_rgb = convert_to_rgb_color(original_rgb, math.floor)
    ceil_code, ceil_rgb = convert_to_rgb_color(original_rgb, math.ceil)

    return {
        "input_hex": hex_color,
        "gray_hex": rgb_to_hex(gray_rgb),
        "color_hex": rgb_to_hex(color_rgb),
        "floor_hex": rgb_to_hex(floor_rgb),
        "ceil_hex": rgb_to_hex(ceil_rgb),
        "input_description": f"HEX: {hex_color}\nRGB: {input_ansi_rgb}",
        "gray_description": format_color_description(gray_code, original_rgb, gray_rgb, color_type, modifiers),
        "color_description": format_color_description(color_code, original_rgb, color_rgb, color_type, modifiers),
        "floor_description": format_color_description(floor_code, original_rgb, floor_rgb, color_type, modifiers),
        "ceil_description": format_color_description(ceil_code, original_rgb, ceil_rgb, color_type, modifiers),
    }


def is_color_bright(hex_color: str) -> bool:
    """Determine if a color is considered bright based on its luminance."""
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return luminance > UI_CONSTANTS["BRIGHTNESS_THRESHOLD"]


class ColorConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_CONSTANTS["CURRENT_DIR"] / "color_converter.ui", self)

        self.current_color = ""
        self.color_type = UI_CONSTANTS["FOREGROUND_CODE"]

        # Connect UI signals
        self.color_picker_button.clicked.connect(self.show_color_dialog)
        self.is_foreground.toggled.connect(self.update_color_type)
        self.reset_modifiers.clicked.connect(self.reset_ui_state)

        for modifier in MODIFIER_CODES:
            getattr(self, modifier).toggled.connect(self.handle_modifier_change)

    @property
    def active_modifiers(self) -> list[str]:
        return get_selected_modifiers(self)

    def update_color_type(self) -> None:
        """Update color type based on foreground/background selection."""
        self.color_type = (
            UI_CONSTANTS["FOREGROUND_CODE"] if self.is_foreground.isChecked() else UI_CONSTANTS["BACKGROUND_CODE"]
        )
        if self.current_color:
            self.update_ui_with_color(self.current_color)

    def handle_modifier_change(self) -> None:
        """Handle changes in modifier checkboxes."""
        if self.current_color:
            self.update_ui_with_color(self.current_color)

    def reset_ui_state(self) -> None:
        """Reset all modifiers to default state."""
        for modifier in MODIFIER_CODES:
            getattr(self, modifier).setChecked(False)
        self.is_foreground.setChecked(True)
        self.update_color_type()

    def update_label_appearance(self, label: QWidget, hex_color: str) -> None:
        """Update label background and text color based on provided hex color."""
        palette = label.palette()
        bg_color = QColor(hex_color)
        text_color = QColor("black" if is_color_bright(hex_color) else "white")

        palette.setColor(QPalette.ColorRole.Window, bg_color)
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        label.setPalette(palette)
        label.setAutoFillBackground(True)

    def update_ui_with_color(self, hex_color: str) -> None:
        """Update all UI elements with new color information."""
        conversion_data = convert_hex_color(hex_color, self.color_type, self.active_modifiers)

        # Update color previews
        self.update_label_appearance(self.in_preview, conversion_data["input_hex"])
        self.update_label_appearance(self.out_gray_preview, conversion_data["gray_hex"])
        self.update_label_appearance(self.out_color_preview, conversion_data["color_hex"])
        self.update_label_appearance(self.out_color_preview_floor, conversion_data["floor_hex"])
        self.update_label_appearance(self.out_color_preview_ceil, conversion_data["ceil_hex"])

        # Update text content
        self.in_preview.setText(conversion_data["input_description"])
        self.out_gray_preview.setText(conversion_data["gray_description"])
        self.out_color_preview.setText(conversion_data["color_description"])
        self.out_color_preview_floor.setText(conversion_data["floor_description"])
        self.out_color_preview_ceil.setText(conversion_data["ceil_description"])

    def show_color_dialog(self) -> None:
        """Show color picker dialog and update UI with selected color."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.update_ui_with_color(self.current_color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorConverterApp()
    window.show()
    sys.exit(app.exec())
