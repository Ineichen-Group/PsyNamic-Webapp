
import re
from plotly.express.colors import sequential
import numpy as np


SECONDARY_COLOR = '#c7c7c7'
TASK2COLOR = {
    "Study Type": sequential.Greens,
    "Study Purpose": sequential.Burg,
    "Study Control": sequential.Peach,
    "Data Type": sequential.Reds,
    "Data Collection": sequential.Mint,
    "Number of Participants": sequential.Bluered,
    "Sex of Participants": sequential.Magenta,
    "Age of Participants": sequential.Teal,
    "Substances": sequential.Purples,
    "Application Form": sequential.Burgyl,
    "Regimen": sequential.Pinkyl,
    "Setting": sequential.Bluyl,
    "Substance Naivety": sequential.Darkmint,
    "Condition": sequential.Oranges,
    "Outcomes": sequential.PuBu,
    "Clinical Trial Phase": sequential.PuBuGn,
    "Study Conclusion": sequential.PuRd,
}

# s. https://plotly.com/python/builtin-colorscales/


def interpolate_color(start: list[int], end: list[int], t: float) -> list[int]:
    """Linearly interpolate between two colors."""
    return [int(s + (e - s) * t) for s, e in zip(start, end)]


def find_luminance_boundaries(start_color, end_color):
    """Find the lightest and darkest colors that still meet the contrast ratio."""
    start_rgb = parse_rgb_string(start_color)
    end_rgb = parse_rgb_string(end_color)

    lightest = start_rgb
    darkest = end_rgb

    for t in np.linspace(0, 1, 100):  # Fine-grained interpolation
        candidate = interpolate_color(start_rgb, end_rgb, t)
        candidate_str = f"rgb({candidate[0]}, {candidate[1]}, {candidate[2]})"
        if check_button_contrast(candidate_str):
            lightest = candidate
            break

    for t in np.linspace(1, 0, 100):  # Fine-grained interpolation in reverse
        candidate = interpolate_color(start_rgb, end_rgb, t)
        candidate_str = f"rgb({candidate[0]}, {candidate[1]}, {candidate[2]})"
        if check_button_contrast(candidate_str):
            darkest = candidate
            break
    return lightest, darkest


def parse_rgb_string(rgb_str):
    """Parses an RGB string like 'rgb(228, 241, 225)' into a tuple of integers."""
    match = re.match(r"^rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)$", rgb_str)
    if not match:
        raise ValueError(f"Invalid RGB string: {rgb_str}")
    return [int(match.group(i)) for i in range(1, 4)]


def rgb_to_hex(rgb: str):
    if rgb.startswith('#'):
        return rgb
    else:
        rgb = rgb.lstrip('rgba')
        int_list = [int(i) for i in rgb.strip('()').split(',')][:3]
        return '#%02x%02x%02x' % tuple(int_list)


def calculate_luminance(color_component):
    """Calculates the luminance of a single RGB component."""
    normalized = float(color_component) / 255
    return normalized / 12.92 if normalized < 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    """Calculates the relative luminance of an RGB color."""
    return (
        0.2126 * calculate_luminance(rgb[0]) +
        0.7152 * calculate_luminance(rgb[1]) +
        0.0722 * calculate_luminance(rgb[2])
    )


def check_button_contrast(background_rgb_str: str) -> bool:
    """
    Checks if white text (#FFFFFF) on the given background color meets WCAG contrast guidelines
    for "minimum contrast large text" (contrast ratio >= 3:1).

    based on: https://github.com/Peter-Slump/python-contrast-ratio
    """

    # Convert background and text colors to RGB
    background_rgb = parse_rgb_string(background_rgb_str)
    text_rgb = [255, 255, 255]  # RGB for white

    # Determine lighter and darker colors
    background_luminance = relative_luminance(background_rgb)
    text_luminance = relative_luminance(text_rgb)

    lighter = max(background_luminance, text_luminance)
    darker = min(background_luminance, text_luminance)

    # Calculate contrast ratio
    contrast_ratio = (lighter + 0.05) / (darker + 0.05)

    # Check if contrast ratio meets the guideline for large text
    return contrast_ratio >= 3


def get_color_mapping(task: str, list_labels: list[str], type: str = 'rgb') -> dict[str, str]:

    if task not in TASK2COLOR:
        raise ValueError(f"Unsupported category: {task}")

    palette_start = TASK2COLOR[task][0]
    palette_end = TASK2COLOR[task][-1]

    lightest, darkest = find_luminance_boundaries(palette_start, palette_end)

    n = len(list_labels)
    if n == 1:
        return {list_labels[0]: palette_end}
    # Extrapolate colors evenly between the lightest and darkest colors
    selected_colors = [
        f"rgb({r}, {g}, {b})"
        for r, g, b in [
            interpolate_color(darkest, lightest, i / (n - 1)) for i in range(n)
        ]
    ]

    # check against contrast ratio
    for color in selected_colors:
        if not check_button_contrast(color):
            raise ValueError(f"Contrast ratio not met for color: {color}")
    if type == 'hex':
        selected_colors = [rgb_to_hex(color) for color in selected_colors]

    return {list_labels[i]: selected_colors[i] for i in range(n)}


def get_color(task: str, type: str = 'rgb') -> str:
    if type == 'hex':
        return rgb_to_hex(TASK2COLOR[task][-1])
    return TASK2COLOR[task][0]
