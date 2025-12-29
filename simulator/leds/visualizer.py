import os
import json
import pygame

LED_RADIUS = 10
DEFAULT_CONFIG = os.path.join("visualizations", "demo_config.json")

WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
OVERLAY_BG = (0, 0, 0, 180)
BORDER_COLOR = (255, 255, 255)


class LEDVisualizer:
    def __init__(self, shared, config_path=None):
        pygame.init()
        pygame.font.init()

        self.shared = shared
        self.config_path = config_path or DEFAULT_CONFIG
        self._load_config()

        self.control_panel_height = 160

        self.min_width = 600
        self.min_height = self.bg_h + self.control_panel_height

        self.screen = pygame.display.set_mode((self.min_width, self.min_height), pygame.RESIZABLE)
        pygame.display.set_caption("Cosplay Fireworks")

        self.bg_image = self.bg_raw.convert_alpha()

        # Fonts
        self.font = pygame.font.SysFont("Segoe UI Emoji", 22)
        self.large_font = pygame.font.SysFont("Segoe UI Emoji", 28)
        self.index_font = pygame.font.SysFont("Segoe UI Emoji", 14)

        self.slider_rect = None
        self.button_rects = {}
        self.clock = pygame.time.Clock()

    def _load_config(self):
        with open(self.config_path, "r") as f:
            cfg = json.load(f)

        bg_path = os.path.join("visualizations", cfg["background"])
        if not os.path.exists(bg_path):
            raise FileNotFoundError(f"Background image not found: {bg_path}")

        self.bg_raw = pygame.image.load(bg_path)
        self.bg_w, self.bg_h = self.bg_raw.get_size()

        self.leds = []
        self.string_map = []
        for string in cfg.get("strings", []):
            default_color = tuple(string.get("default_color", [0, 0, 0]))
            idx_start = len(self.leds)
            for i, led in enumerate(string.get("leds", [])):
                self.leds.append({
                    "x_pct": float(led["x"]),
                    "y_pct": float(led["y"]),
                    "color": (0, 0, 0),
                    "default_color": default_color,
                    "index": i,
                    "string": string.get("name", f"string{len(self.string_map)}")
                })
            # Keep track of string boundaries for labeling if needed
            self.string_map.append((string.get("name", f"string{len(self.string_map)}"),
                                    idx_start,
                                    len(string.get("leds", []))))

        self.custom_labels = [btn.get("label", "") for btn in cfg.get("buttons", [])]

    def update_leds(self, colors):
        for i, c in enumerate(colors):
            if i < len(self.leds):
                self.leds[i]["color"] = c

    def handle_events(self):
        clicked = None
        seek_drag = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.shared.clicked_button = "exit"
            elif e.type == pygame.VIDEORESIZE:
                self._resize_window(e.w, e.h)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                for name, rect in self.button_rects.items():
                    if rect.collidepoint(mx, my):
                        clicked = name
                if self.slider_rect and self.slider_rect.collidepoint(mx, my):
                    seek_drag = True

        return clicked, seek_drag

    def _resize_window(self, w, h):
        new_w = max(w, self.min_width)
        new_h = max(h, self.min_height)
        self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)

    def draw(self):
        win_w, win_h = self.screen.get_size()

        # Determine image area
        img_space_h = win_h - self.control_panel_height

        scale_w = win_w
        scale_h = int(scale_w * (self.bg_h / self.bg_w))

        if scale_h > img_space_h:
            scale_h = img_space_h
            scale_w = int(scale_h * (self.bg_w / self.bg_h))

        img_x = (win_w - scale_w) // 2
        img_y = 0

        scaled_bg = pygame.transform.smoothscale(self.bg_image, (scale_w, scale_h))
        self.screen.blit(scaled_bg, (img_x, img_y))

        # Draw LEDs + optional index
        for led in self.leds:
            x = int(led["x_pct"] * win_w)
            y = int(led["y_pct"] * win_h)

            if self.shared.is_paused:
                color = led["default_color"]
            else:
                color = led["color"]

            pygame.draw.circle(self.screen, color, (x, y), LED_RADIUS)

            if self.shared.is_paused:
                # Compute luminance for contrast
                r, g, b = color
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                font_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)

                font = pygame.font.SysFont("Arial", 10)
                label_surface = font.render(str(led["index"]), True, font_color)
                label_rect = label_surface.get_rect(center=(x, y))
                self.screen.blit(label_surface, label_rect)


        # Draw control panel
        panel_w = int(win_w * 0.95)
        panel_h = self.control_panel_height - 10
        panel_x = (win_w - panel_w) // 2
        panel_y = win_h - panel_h - 10

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(OVERLAY_BG)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, BORDER_COLOR, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

        self.button_rects.clear()

        # Track name centered
        track_text = self.large_font.render(self.shared.current_track_name, True, WHITE)
        self.screen.blit(track_text, (panel_x + (panel_w - track_text.get_width()) // 2, panel_y + 10))

        # Playback buttons
        icons = [("prev", "⏮️"), ("pause", "⏯️"), ("next", "⏭️"), ("exit", "❌")]
        playback_surfs = [self.large_font.render(icon, True, WHITE) for (_, icon) in icons]

        # Soft button surfaces
        soft_surfs = [self.font.render(lbl, True, WHITE) for lbl in self.custom_labels]

        # Compute row widths
        playback_row_width = (sum(s.get_width() for s in playback_surfs)
                              + (len(playback_surfs) - 1) * 20)
        soft_row_width = (sum(s.get_width() for s in soft_surfs)
                          + (len(soft_surfs) - 1) * 20) if soft_surfs else 0
        content_width = max(playback_row_width, soft_row_width, 200)

        # Playback row
        row_y = panel_y + 40
        start_x = panel_x + (panel_w - playback_row_width) // 2
        x = start_x
        for (key, _), surf in zip(icons, playback_surfs):
            rect = surf.get_rect(topleft=(x, row_y))
            self.screen.blit(surf, rect)
            self.button_rects[key] = rect
            x += surf.get_width() + 20

        # Soft buttons row
        soft_y = row_y + self.large_font.get_height() + 10
        if soft_surfs:
            start_soft_x = panel_x + (panel_w - soft_row_width) // 2
            x2 = start_soft_x
            for lbl, surf in zip(self.custom_labels, soft_surfs):
                rect = surf.get_rect(topleft=(x2, soft_y))
                self.screen.blit(surf, rect)
                self.button_rects[lbl] = rect
                x2 += surf.get_width() + 20

        # Slider
        slider_y = soft_y + self.font.get_height() + 18
        slider_w = content_width
        slider_x = panel_x + (panel_w - slider_w) // 2
        self.slider_rect = pygame.Rect(slider_x, slider_y, slider_w, 10)
        pygame.draw.rect(self.screen, GRAY, self.slider_rect)
        handle_x = int(self.slider_rect.x + self.shared.seek_position * self.slider_rect.width)
        pygame.draw.circle(self.screen, WHITE, (handle_x, self.slider_rect.y + 5), 8)

        pygame.display.flip()
        self.clock.tick(60)
