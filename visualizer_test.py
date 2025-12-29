import time
from simulator.leds.visualizer import LEDVisualizer

vis = LEDVisualizer(led_count=24)

colors = [(255, 0, 0)] * 24  # Red test

running = True
start = time.time()

while running and time.time() - start < 5:
    running = vis.handle_events()
    vis.update(colors)
