# simulator/leds/patterns.py

from simulator.leds.eq_colors import get_eq_band_colors

def blend_bands_to_led_color(band_energies, band_colors):
    """
    Multiply each RGB color by its corresponding intensity and sum them.
    Result is one blended (R, G, B) color.
    """
    r, g, b = 0.0, 0.0, 0.0
    for intensity, color in zip(band_energies, band_colors):
        r += intensity * color[0]
        g += intensity * color[1]
        b += intensity * color[2]

    # Clamp to [0, 255]
    r = min(int(r), 255)
    g = min(int(g), 255)
    b = min(int(b), 255)

    return (r, g, b)


def blended_eq_pattern(band_energies, led_count=24):
    """
    Returns a list of blended RGB values, one per LED.
    For now, all LEDs get the same color. We'll add variations later.
    """
    band_colors = get_eq_band_colors()
    color = blend_bands_to_led_color(band_energies, band_colors)
    return [color] * led_count
