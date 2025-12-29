from simulator.leds.patterns import eq_to_rgb_pattern

bands = {"bass": 0.8, "mid": 0.4, "treble": 0.2}
colors = eq_to_rgb_pattern(bands, led_count=5)

for i, c in enumerate(colors):
    print(f"LED {i}: RGB{c}")
