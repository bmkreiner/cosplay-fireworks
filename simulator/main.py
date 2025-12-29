import os
import re
import time
import pygame
import numpy as np
from pydub import AudioSegment
import simpleaudio as sa

from simulator.audio.equalizer import Equalizer10Band
from simulator.leds.visualizer import LEDVisualizer
from simulator.leds.patterns import blended_eq_pattern

AUDIO_DIR = "audio_library"
CHUNK = 1024


class SharedState:
    def __init__(self, custom_labels):
        self.seek_position = 0.0
        self.user_seek_active = False
        self.clicked_button = None
        self.current_track_name = ""
        self.is_paused = False
        self.custom_labels = custom_labels


def get_playlist():
    pattern = re.compile(r"^(\d+)\.\s+.+\.mp3$", re.I)
    files = []
    for f in os.listdir(AUDIO_DIR):
        m = pattern.match(f)
        if m:
            files.append((int(m.group(1)), f))
    return [f for _, f in sorted(files)]


def load_audio(fname):
    path = os.path.join(AUDIO_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    audio = AudioSegment.from_file(path, format="mp3")
    audio = audio.set_channels(1).set_frame_rate(44100)
    samples = np.array(audio.get_array_of_samples()).astype(np.int16)
    return samples, audio.frame_rate


def main():
    playlist = get_playlist()
    if not playlist:
        print("[ERROR] No valid MP3 files found in 'audio_library' folder.")
        time.sleep(3)
        return

    print(f"[INFO] Playlist loaded: {playlist}")

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
            try:
                playback = sa.play_buffer(samples[pos:].tobytes(), 1, 2, sr)
            except Exception as e:
                print(f"[AUDIO ERROR] Could not start playback: {e}")
                playback = None

    state.current_track_name = playlist[index]
    start_audio(0)

    visualizer = LEDVisualizer(state, cfg_path)

    running = True
    while running:
        clicked, seek_drag = visualizer.handle_events()

        # Handle clicked controls
        if clicked:
            state.clicked_button = clicked

        # Button actions
        action = state.clicked_button
        state.clicked_button = None

        if action == "exit":
            print("[INFO] Exit requested by user.")
            running = False
            break
        elif action == "pause":
            state.is_paused = not state.is_paused
            print(f"[INFO] Paused: {state.is_paused}")
            if state.is_paused and playback:
                playback.stop()
            if not state.is_paused:
                start_audio(position)

        elif action == "next":
            index = (index + 1) % len(playlist)
            samples, sr = load_audio(playlist[index])
            eq = Equalizer10Band(sr)
            position = 0
            state.current_track_name = playlist[index]
            print(f"[INFO] Switched to next track: {state.current_track_name}")
            if not state.is_paused:
                start_audio(position)

        elif action == "prev":
            index = (index - 1) % len(playlist)
            samples, sr = load_audio(playlist[index])
            eq = Equalizer10Band(sr)
            position = 0
            state.current_track_name = playlist[index]
            print(f"[INFO] Switched to previous track: {state.current_track_name}")
            if not state.is_paused:
                start_audio(position)

        # Seek interaction
        if seek_drag:
            mx = pygame.mouse.get_pos()[0]
            r = visualizer.slider_rect
            if r and r.collidepoint(mx, r.y):
                state.seek_position = (mx - r.x) / r.width
                position = int(state.seek_position * len(samples))
                print(f"[SEEK] Jumped to {state.seek_position:.2%}")
                start_audio(position)

        # EQ + LED Processing
        if not state.is_paused and position + CHUNK < len(samples):
            chunk = samples[position:position + CHUNK].astype(np.float32)
            bands = eq.process(chunk)
            colors = blended_eq_pattern(bands, len(visualizer.leds))
            position += CHUNK
        else:
            colors = [(0, 0, 0)] * len(visualizer.leds)

        state.seek_position = position / len(samples)
        visualizer.update_leds(colors)
        visualizer.draw()

        time.sleep(CHUNK / sr)

    if playback:
        playback.stop()
    pygame.quit()
    print("[INFO] Program exited cleanly.")


if __name__ == "__main__":
    main()
