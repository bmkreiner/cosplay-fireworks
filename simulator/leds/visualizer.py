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

        self.font = pygame.font.SysFont("Segoe UI Emoji", 22)
        self.large_font = pygame.font.SysFont("Segoe UI Emoji", 28)
        self.index_font = pygame.font.SysFont("Segoe UI Emoji", 14)

        self.slider_rect = None
        self.button_rects = {}
        self.clock = pygame.time.Clock()

        self.dragging_led = None
        self.dirty = False

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
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
            self.string_map.append((string.get("name", f"string{len(self.string_map)}"),
                                    idx_start,
                                    len(string.get("leds", []))))

        self.custom_labels = [btn.get("label", "") for btn in cfg.get("buttons", [])]

    def save_config(self):
        # Rewrite JSON with updated led positions
        new_strings = []
        for name, start, count in self.string_map:
            leds = self.leds[start:start + count]
            led_entries = [{"x": round(led["x_pct"], 4), "y": round(led["y_pct"], 4)} for led in leds]
            default_color = leds[0]["default_color"] if leds else [0, 0, 0]
            new_strings.append({
                "name": name,
                "default_color": list(default_color),
                "leds": led_entries
            })

        data = {
            "background": os.path.basename(self.config_path).replace(".json", ".png"),
            "strings": new_strings,
            "buttons": [{"label": lbl} for lbl in self.custom_labels]
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.dirty = False

    def update_leds(self, colors):
        for i, c in enumerate(colors):
            if i < len(self.leds):
                self.leds[i]["color"] = c

    def handle_events(self):
        clicked = None
        seek_drag = False
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                clicked = "exit"

            elif e.type == pygame.VIDEORESIZE:
                self._resize_window(e.w, e.h)

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if self.shared.edit_mode:
                    # In edit mode: allow dragging, save, or exit only
                    if "save" in self.button_rects and self.button_rects["save"].collidepoint(mx, my):
                        clicked = "save"
                    elif "edit" in self.button_rects and self.button_rects["edit"].collidepoint(mx, my):
                        clicked = "edit"
                    else:
                        # Check for LED under cursor
                        for i, led in enumerate(self.leds):
                            x, y = self._led_screen_position(led)
                            if pygame.Rect(x - LED_RADIUS, y - LED_RADIUS, 2 * LED_RADIUS, 2 * LED_RADIUS).collidepoint(mx, my):
                                self.dragging_led = i
                                break

                else:
                    # Normal mode: allow all buttons
                    for name, rect in self.button_rects.items():
                        if rect.collidepoint(mx, my):
                            clicked = name
                    if self.slider_rect and self.slider_rect.collidepoint(mx, my):
                        seek_drag = True

            elif e.type == pygame.MOUSEBUTTONUP:
                self.dragging_led = None

            elif e.type == pygame.MOUSEMOTION:
                if self.shared.edit_mode and self.dragging_led is not None:
                    img_x, img_y, img_w, img_h = self.image_rect
                    rel_x = (mx - img_x) / img_w
                    rel_y = (my - img_y) / img_h
                    rel_x = min(max(0.0, rel_x), 1.0)
                    rel_y = min(max(0.0, rel_y), 1.0)
                    led = self.leds[self.dragging_led]
                    led["x_pct"] = rel_x
                    led["y_pct"] = rel_y
                    self.dirty = True

        return clicked, seek_drag

   
    def _resize_window(self, w, h):
        new_w = max(w, self.min_width)
        new_h = max(h, self.min_height)
        self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)

    def _led_screen_position(self, led):
        img_x, img_y, img_w, img_h = self.image_rect
        led_x = img_x + int(led["x_pct"] * img_w)
        led_y = img_y + int(led["y_pct"] * img_h)
        return led_x, led_y

    def draw(self):
        win_w, win_h = self.screen.get_size()
        img_space_h = win_h - self.control_panel_height

        scale_w = win_w
        scale_h = int(scale_w * (self.bg_h / self.bg_w))
        if scale_h > img_space_h:
            scale_h = img_space_h
            scale_w = int(scale_h * (self.bg_w / self.bg_h))

        img_x = (win_w - scale_w) // 2
        img_y = 0
        self.image_rect = (img_x, img_y, scale_w, scale_h)

        scaled_bg = pygame.transform.smoothscale(self.bg_image, (scale_w, scale_h))
        self.screen.blit(scaled_bg, (img_x, img_y))

        for led in self.leds:
            x, y = self._led_screen_position(led)
            color = led["default_color"] if self.shared.is_paused else led["color"]
            pygame.draw.circle(self.screen, color, (x, y), LED_RADIUS)

            if self.shared.is_paused:
                r, g, b = color
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                font_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)
                label_surface = self.index_font.render(str(led["index"]), True, font_color)
                self.screen.blit(label_surface, label_surface.get_rect(center=(x, y)))

        # CONTROL PANEL
        panel_w = int(win_w * 0.95)
        panel_h = self.control_panel_height - 10
        panel_x = (win_w - panel_w) // 2
        panel_y = win_h - panel_h - 10

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(OVERLAY_BG)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, BORDER_COLOR, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

        self.button_rects.clear()

        # Track name
        track_text = self.large_font.render(self.shared.current_track_name, True, WHITE)
        self.screen.blit(track_text, (panel_x + (panel_w - track_text.get_width()) // 2, panel_y + 10))

        # Buttons
        buttons = [("prev", "⏮️"), ("pause", "⏯️"), ("next", "⏭️")]
        if self.shared.edit_mode:
            if self.dirty:
                buttons.append(("save", "💾"))
            buttons.append(("edit", "❌"))  # acts like cancel/exit edit
        else:
            buttons.append(("edit", "✏️"))


        btn_surfs = [self.large_font.render(icon, True, WHITE) for _, icon in buttons]
        row_w = sum(s.get_width() + 20 for s in btn_surfs) - 20
        x = panel_x + (panel_w - row_w) // 2
        row_y = panel_y + 40

        for (name, _), surf in zip(buttons, btn_surfs):
            rect = surf.get_rect(topleft=(x, row_y))
            self.screen.blit(surf, rect)
            if not self.shared.in_effect:
                self.button_rects[name] = rect
            x += surf.get_width() + 20

        # Soft buttons
        soft_surfs = [self.font.render(lbl, True, WHITE) for lbl in self.custom_labels]
        if soft_surfs:
            soft_row_w = sum(s.get_width() + 20 for s in soft_surfs) - 20
            x = panel_x + (panel_w - soft_row_w) // 2
            y = row_y + self.large_font.get_height() + 10
            for lbl, surf in zip(self.custom_labels, soft_surfs):
                rect = surf.get_rect(topleft=(x, y))
                self.screen.blit(surf, rect)
                self.button_rects[lbl] = rect
                x += surf.get_width() + 20

        # Slider
        slider_y = panel_y + panel_h - 30
        slider_w = panel_w // 2
        slider_x = panel_x + (panel_w - slider_w) // 2
        self.slider_rect = pygame.Rect(slider_x, slider_y, slider_w, 10)
        pygame.draw.rect(self.screen, GRAY, self.slider_rect)
        handle_x = int(self.slider_rect.x + self.shared.seek_position * self.slider_rect.width)
        pygame.draw.circle(self.screen, WHITE, (handle_x, self.slider_rect.y + 5), 8)

        pygame.display.flip()
        self.clock.tick(60)
