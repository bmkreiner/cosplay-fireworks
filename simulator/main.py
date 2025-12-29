import os
import re
import time
import threading
import tkinter as tk
import numpy as np
import pygame
from pydub import AudioSegment
import simpleaudio as sa

from simulator.audio.equalizer import Equalizer10Band
from simulator.leds.visualizer import LEDVisualizer
from simulator.controls.control_panel import ControlPanel
from simulator.leds.patterns import blended_eq_pattern

AUDIO_DIR = "audio_library"
CHUNK = 1024


class SharedState:
    def __init__(self, custom_labels):
        self.seek_position = 0.0
        self.user_seek_active = False
        self.clicked_button = None
        self.current_track_name = ""
        self.exit_flag = False
        self.is_paused = False
        self.custom_labels = custom_labels


def get_playlist():
    pat = re.compile(r"^(\d+)\.\s+.+\.mp3$", re.I)
    files = []
    for f in os.listdir(AUDIO_DIR):
        m = pat.match(f)
        if m:
            files.append((int(m.group(1)), f))
    return [f for _, f in sorted(files)]


def load_audio(fname):
    path = os.path.join(AUDIO_DIR, fname)
    audio = AudioSegment.from_file(path, format="mp3")
    audio = audio.set_channels(1).set_frame_rate(44100)
    samples = np.array(audio.get_array_of_samples()).astype(np.int16)
    return samples, audio.frame_rate


def main():
    playlist = get_playlist()
    if not playlist:
        print("No valid MP3 files in audio_library.")
        return

    import json
    cfg_path = os.path.join("visualizations", "demo_config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)

    custom_labels = [b["label"] for b in cfg.get("buttons", [])]
    state = SharedState(custom_labels)

    index = 0
    samples, sr = load_audio(playlist[index])
    eq = Equalizer10Band(sr)
    position = 0
    playback = None

    def start_audio(pos):
        nonlocal playback
        if playback:
            playback.stop()
        if 0 <= pos < len(samples):
            playback = sa.play_buffer(samples[pos:].tobytes(), 1, 2, sr)
        else:
            playback = None

    state.current_track_name = playlist[index]
    start_audio(0)

    visualizer = LEDVisualizer(state, cfg_path)

    root = tk.Tk()
    root.withdraw()
    ControlPanel(root, state)

    def loop():
        nonlocal position, samples, sr, eq, index, playback
        while not state.exit_flag:
            action = state.clicked_button
            state.clicked_button = None

            if action == "exit":
                if playback:
                    playback.stop()
                state.exit_flag = True
                break

            if action == "pause":
                state.is_paused = not state.is_paused
                if playback:
                    playback.stop()
                if not state.is_paused:
                    start_audio(position)

            elif action == "next":
                index = (index + 1) % len(playlist)
                samples, sr = load_audio(playlist[index])
                eq = Equalizer10Band(sr)
                position = 0
                state.current_track_name = playlist[index]
                if not state.is_paused:
                    start_audio(0)

            elif action == "prev":
                index = (index - 1) % len(playlist)
                samples, sr = load_audio(playlist[index])
                eq = Equalizer10Band(sr)
                position = 0
                state.current_track_name = playlist[index]
                if not state.is_paused:
                    start_audio(0)

            if state.user_seek_active:
                try:
                    new_pos = int(float(state.seek_position) * len(samples))
                    if 0 <= new_pos < len(samples):
                        position = new_pos
                        if not state.is_paused:
                            start_audio(position)
                except Exception as e:
                    print(f"[SEEK ERROR] {e}")
                finally:
                    state.user_seek_active = False

            # Process audio frame
            if not state.is_paused and position + CHUNK < len(samples):
                chunk = samples[position:position + CHUNK].astype(np.float32)
                bands = eq.process(chunk)
                colors = blended_eq_pattern(bands, len(visualizer.leds))
                position += CHUNK
            else:
                colors = [(0, 0, 0)] * len(visualizer.leds)

            visualizer.update_leds(colors)
            visualizer.run_once()

            if not state.is_paused:
                state.seek_position = position / len(samples)

            time.sleep(CHUNK / sr)

        # Cleanup
        if playback:
            playback.stop()
        pygame.quit()
        time.sleep(0.2)

    threading.Thread(target=loop, daemon=True).start()
    root.mainloop()
    state.exit_flag = True


if __name__ == "__main__":
    main()
