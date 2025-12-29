from simulator.leds.patterns import blended_eq_pattern

# Fake test: equal energy in all bands
test_bands = [1.0] * 10  # max intensity
leds = blended_eq_pattern(test_bands, led_count=5)

for i, c in enumerate(leds):
    print(f"LED {i}: RGB{c}")
