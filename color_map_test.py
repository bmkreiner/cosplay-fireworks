from simulator.leds.eq_colors import get_eq_band_colors

colors = get_eq_band_colors()
for i, color in enumerate(colors):
    print(f"Band {i}: RGB{color}")
