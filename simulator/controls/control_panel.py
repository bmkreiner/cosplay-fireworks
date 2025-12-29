import tkinter as tk
from tkinter import ttk


class ControlPanel(tk.Toplevel):
    def __init__(self, master, shared):
        super().__init__(master)
        self.shared = shared
        self.title("Cosplay Fireworks – Controls")

        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        emoji_font = ("Segoe UI Emoji", 20)

        # --- Track label ---
        self.track_label = ttk.Label(self, text="", font=("Segoe UI", 11))
        self.track_label.grid(row=0, column=0, columnspan=4, pady=(10, 5))

        # --- Slider ---
        self.seek_var = tk.DoubleVar()
        self.slider = ttk.Scale(
            self, from_=0.0, to=1.0, variable=self.seek_var, command=self._on_seek
        )
        self.slider.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10)

        # --- Playback Buttons (using emoji) ---
        emoji_map = {
            "prev": "⏮️",
            "pause": "⏯️",
            "next": "⏭️",
            "exit": "❌"
        }

        for i, action in enumerate(emoji_map):
            btn = tk.Button(
                self,
                text=emoji_map[action],
                font=emoji_font,
                width=3,
                command=lambda a=action: self._on_button(a)
            )
            btn.grid(row=2, column=i, padx=5, pady=6)

        # --- Custom Buttons ---
        self.custom_frame = ttk.Frame(self)
        self.custom_frame.grid(row=3, column=0, columnspan=4, pady=(5, 10))

        for label in shared.custom_labels:
            ttk.Button(
                self.custom_frame,
                text=label,
                command=lambda l=label: self._on_button(l)
            ).pack(side="left", padx=4)

        # Lock window size to current content
        self.update_idletasks()
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}")
        self.resizable(False, False)

        self.after(30, self._sync_loop)

    def _sync_loop(self):
        self.track_label.config(text=self.shared.current_track_name)
        if not self.shared.user_seek_active:
            self.seek_var.set(self.shared.seek_position)
        self.after(30, self._sync_loop)

    def _on_seek(self, _):
        self.shared.user_seek_active = True
        self.shared.seek_position = self.seek_var.get()

    def _on_button(self, action):
        self.shared.clicked_button = action

    def _on_exit(self):
        self.shared.exit_flag = True
        self.destroy()
