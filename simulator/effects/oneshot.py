import math
import time
import random


def flash_effect(leds, elapsed):
    """All LEDs flash white once for 0.2 seconds."""
    duration = 0.2
    color = (255, 255, 255) if elapsed < duration else (0, 0, 0)
    return [color] * len(leds), elapsed >= duration


def strobe_effect(leds, elapsed):
    """Flashes on/off quickly 5 times in 1 second."""
    strobe_count = 5
    total_duration = 1.0
    interval = total_duration / (strobe_count * 2)

    if elapsed >= total_duration:
        return [(0, 0, 0)] * len(leds), True

    is_on = int(elapsed / interval) % 2 == 0
    color = (255, 255, 255) if is_on else (0, 0, 0)
    return [color] * len(leds), False


def pulse_effect(leds, elapsed):
    """Smooth pulsing brightness white light."""
    duration = 2.0
    if elapsed >= duration:
        return [(0, 0, 0)] * len(leds), True

    brightness = (math.sin(elapsed * math.pi / duration) + 1) / 2  # 0 → 1
    level = int(255 * brightness)
    return [(level, level, level)] * len(leds), False


def ripple_effect(leds, elapsed):
    """A white ripple expands from center LED."""
    total_duration = 1.5
    if elapsed > total_duration:
        return [(0, 0, 0)] * len(leds), True

    # Find image-space coordinates
    coords = [(led["x_pct"], led["y_pct"]) for led in leds]

    # Compute approximate center
    cx = sum(x for x, _ in coords) / len(coords)
    cy = sum(y for _, y in coords) / len(coords)

    max_dist = max(math.hypot(x - cx, y - cy) for x, y in coords)
    wave_radius = elapsed * 1.5  # Speed of ripple
    ring_width = 0.05  # thickness of the ripple band

    colors = []
    for x_pct, y_pct in coords:
        dx = x_pct - cx
        dy = y_pct - cy
        dist = math.hypot(dx, dy)

        if abs(dist - wave_radius) < ring_width:
            colors.append((255, 255, 255))
        else:
            colors.append((0, 0, 0))

    return colors, False



