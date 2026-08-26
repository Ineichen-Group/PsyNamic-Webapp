
import re

import numpy as np
from plotly.express.colors import sequential

GREY = '#c7c7c7'
BROWN = "#e5d8bd"
BLUE = "#b6c2d1"

# Matches the plot_bgcolor used for charts in components/graphs.py.
CHART_BACKGROUND = "#f8f8f8"

SECONDARY_COLOR = '#e5ecf6'
TASK2COLOR = {
    "Study Type": sequential.Greens,
    "Study Purpose": sequential.Teal,
    "Study Control": sequential.Burg,
    "Data Type": sequential.Reds,
    "Data Collection": sequential.Magenta,
    "Number of Participants": sequential.Bluered,
    "Sex of Participants": sequential.Mint,
    "Age of Participants": sequential.Sunsetdark,
    "Substances": sequential.Purples,
    "Application Form": sequential.Burgyl,
    "Regimen": sequential.Brwnyl,
    "Setting": sequential.PuBu,
    "Substance Naivety": sequential.Darkmint,
    "Condition": sequential.Oranges,
    "Outcomes": sequential.Bluyl,
    # "Clinical Trial Phase": sequential.PuBuGn,
    # "Study Conclusion": sequential.PuRd,
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


def hex_to_rgb(hex_color: str) -> str:
    """Convert a hex color string to an RGB string."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


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


def contrast_ratio(rgb_a: list[int], rgb_b: list[int]) -> float:
    """Computes the WCAG contrast ratio between two RGB colors."""
    luminance_a = relative_luminance(rgb_a)
    luminance_b = relative_luminance(rgb_b)
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def check_button_contrast(background_rgb_str: str) -> bool:
    """
    Checks if white text (#FFFFFF) on the given background color meets WCAG contrast guidelines
    for "minimum contrast large text" (contrast ratio >= 3:1).

    based on: https://github.com/Peter-Slump/python-contrast-ratio
    """
    background_rgb = parse_rgb_string(background_rgb_str)
    return contrast_ratio(background_rgb, [255, 255, 255]) >= 3


def find_max_lightness_ratio(end_rgb: list[int], start_rgb: list[int], background_rgb: list[int], min_ratio: float = 1.8) -> float:
    """Finds how far (0..1) to interpolate from `end_rgb` (dark) towards `start_rgb` (light)
    while the resulting color still keeps at least `min_ratio` contrast against `background_rgb`."""
    max_t = 0.0
    for t in np.linspace(0, 1, 100):
        candidate = interpolate_color(end_rgb, start_rgb, t)
        if contrast_ratio(candidate, background_rgb) < min_ratio:
            break
        max_t = t
    return max_t


def get_color_mapping(task: str, list_labels: list[str], type: str = 'rgb') -> dict[str, str]:

    if task not in TASK2COLOR:
        raise ValueError(f"Unsupported category: {task}")

    palette_start = TASK2COLOR[task][0]
    palette_end = TASK2COLOR[task][-1]

    # Use as much of the palette's lightness range as possible (not just the subset that
    # is safe for white text) so many categories remain visually distinguishable; text
    # color is chosen per swatch instead (see `get_text_color`).
    start_rgb = parse_rgb_string(palette_start)
    end_rgb = parse_rgb_string(palette_end)
    background_rgb = parse_rgb_string(hex_to_rgb(CHART_BACKGROUND))

    # Treat certain labels as special (use gray) and do not include them in
    # the interpolated palette so spacing of colors for real categories stays even.
    special_labels = {"Unknown", "Not applicable", "Other"}
    non_special = [lbl for lbl in list_labels if lbl not in special_labels]
    # If all labels are special, return gray for all
    if len(non_special) == 0:
        return {lbl: hex_to_rgb(GREY) for lbl in list_labels}

    n = len(non_special)
    if n == 1:
        selected_colors = [f"rgb({end_rgb[0]}, {end_rgb[1]}, {end_rgb[2]})"]
    else:
        # Interpolate evenly across the whole palette range (darkest -> lightest stop),
        # capping how far we go towards the lightest stop so it stays visible against the
        # actual chart/page background instead of fading into it.
        lightness_cap = find_max_lightness_ratio(end_rgb, start_rgb, background_rgb)
        selected_colors = [
            "rgb({}, {}, {})".format(
                *interpolate_color(end_rgb, start_rgb, (i / (n - 1)) * lightness_cap)
            )
            for i in range(n)
        ]

    # convert to hex when requested
    if type == 'hex':
        selected_colors = [rgb_to_hex(color) for color in selected_colors]

    # Build final mapping preserving original order; assign gray to special labels
    mapping = {}
    idx = 0
    for lbl in list_labels:
        if lbl in special_labels:
            mapping[lbl] = hex_to_rgb(GREY) if type != 'hex' else hex_to_rgb(GREY)
        else:
            mapping[lbl] = selected_colors[idx]
            idx += 1

    return mapping


def get_text_color(rgb_or_hex: str) -> str:
    """Returns '#FFFFFF' or '#000000', whichever gives sufficient contrast against the given background color."""
    rgb = parse_rgb_string(rgb_or_hex) if not rgb_or_hex.startswith('#') else parse_rgb_string(hex_to_rgb(rgb_or_hex))
    return "#FFFFFF" if relative_luminance(rgb) < 0.42 else "#000000"


def get_color(task: str, type: str = 'rgb') -> str:
    if type == 'hex':
        return rgb_to_hex(TASK2COLOR[task][-1])
    return TASK2COLOR[task][0]
