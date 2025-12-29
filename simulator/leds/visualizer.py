import os
import json
import pygame

LED_RADIUS = 10
DEFAULT_CONFIG = os.path.join("visualizations", "demo_config.json")


class LEDVisualizer:
    def __init__(self, shared, config_path=None):
        pygame.init()

        self.shared = shared
        self.config_path = config_path or DEFAULT_CONFIG

        # Load config + RAW image only (NO convert here)
        self._load_config()

        # Aspect ratio from raw image
        self.aspect_ratio = self.bg_width / self.bg_height

        # Create window FIRST (required before convert)
        self.window_size = (self.bg_width, self.bg_height)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Cosplay Fireworks – Visualizer")

        # NOW it is safe to convert
        self.bg_image = self.bg_image_raw.convert_alpha()

        self.clock = pygame.time.Clock()

    def _load_config(self):
        with open(self.config_path, "r") as f:
            cfg = json.load(f)

        bg_path = os.path.join("visualizations", cfg["background"])
        if not os.path.exists(bg_path):
            raise FileNotFoundError(bg_path)

        # Load RAW image only
        self.bg_image_raw = pygame.image.load(bg_path)
        self.bg_width, self.bg_height = self.bg_image_raw.get_size()

        self.leds = []
        for string in cfg.get("strings", []):
            for led in string.get("leds", []):
                self.leds.append({
                    "x_pct": float(led["x"]),
                    "y_pct": float(led["y"]),
                    "color": (0, 0, 0)
                })

    def update_leds(self, colors):
        for i, color in enumerate(colors):
            if i < len(self.leds):
                self.leds[i]["color"] = color

    def _resize_window(self, new_w, new_h):
        # Aspect-locked resize
        if new_w <= 0 or new_h <= 0:
            return

        if (new_w / new_h) > self.aspect_ratio:
            new_w = int(new_h * self.aspect_ratio)
        else:
            new_h = int(new_w / self.aspect_ratio)

        if (new_w, new_h) != self.window_size:
            self.window_size = (new_w, new_h)
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def run_once(self):
        if self.shared.exit_flag:
            pygame.quit()
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.shared.exit_flag = True
            elif event.type == pygame.VIDEORESIZE:
                self._resize_window(event.w, event.h)

        self._draw()

    def _draw(self):
        try:
            win_w, win_h = self.window_size

            bg = pygame.transform.smoothscale(
                self.bg_image, (win_w, win_h)
            )
            self.screen.blit(bg, (0, 0))

            for led in self.leds:
                x = int(led["x_pct"] * win_w)
                y = int(led["y_pct"] * win_h)
                pygame.draw.circle(
                    self.screen, led["color"], (x, y), LED_RADIUS
                )

            pygame.display.flip()
            self.clock.tick(60)

        except Exception as e:
            # Absolute last-resort safety
            print(f"[Visualizer ERROR] {e}")
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
