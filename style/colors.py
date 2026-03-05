
import re
from plotly.express.colors import sequential
import numpy as np


SECONDARY_COLOR = '#c7c7c7'
TASK2COLOR = {
    "Study Type": sequential.Greens,
    "Study Purpose": sequential.Teal,
    "Study Control": sequential.Burg,
    "Data Type": sequential.Reds,
    "Data Collection": sequential.Magenta,
    "Number of Participants": sequential.Bluered,
    "Sex of Participants": sequential.Mint,
    "Age of Participants": sequential.Peach,
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

    # Treat certain labels as special (use gray) and do not include them in
    # the interpolated palette so spacing of colors for real categories stays even.
    special_labels = {"Unknown", "Not applicable"}
    non_special = [lbl for lbl in list_labels if lbl not in special_labels]

    # If all labels are special, return gray for all
    if len(non_special) == 0:
        return {lbl: SECONDARY_COLOR for lbl in list_labels}

    n = len(non_special)
    if n == 1:
        palette = [palette_end]
    else:
        # Extrapolate colors evenly between the darkest and lightest colors
        palette = [
            interpolate_color(darkest, lightest, i / (n - 1)) for i in range(n)
        ]

    # convert to rgb() strings
    selected_colors = [f"rgb({r}, {g}, {b})" for r, g, b in palette]

    # check against contrast ratio for generated colors only
    for color in selected_colors:
        if not check_button_contrast(color):
            raise ValueError(f"Contrast ratio not met for color: {color}")

    # convert to hex when requested
    if type == 'hex':
        selected_colors = [rgb_to_hex(color) for color in selected_colors]

    # Build final mapping preserving original order; assign gray to special labels
    mapping = {}
    idx = 0
    for lbl in list_labels:
        if lbl in special_labels:
            mapping[lbl] = SECONDARY_COLOR if type != 'hex' else SECONDARY_COLOR
        else:
            mapping[lbl] = selected_colors[idx]
            idx += 1

    return mapping


def get_color(task: str, type: str = 'rgb') -> str:
    if type == 'hex':
        return rgb_to_hex(TASK2COLOR[task][-1])
    return TASK2COLOR[task][0]
