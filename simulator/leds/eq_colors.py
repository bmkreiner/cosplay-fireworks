# simulator/leds/eq_colors.py

def get_eq_band_colors():
    """
    Returns a list of 10 RGB tuples representing spectral colors,
    mapped from lowest to highest EQ bands.
    """
    return [
        (255, 0, 0),      # Red
        (255, 64, 0),     # Red-Orange
        (255, 128, 0),    # Orange
        (255, 255, 0),    # Yellow
        (128, 255, 0),    # Yellow-Green
        (0, 255, 0),      # Green
        (0, 255, 128),    # Cyan
        (0, 128, 255),    # Blue-Green
        (0, 0, 255),      # Blue
        (128, 0, 255),    # Violet
    ]
