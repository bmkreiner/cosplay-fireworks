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
from simulator.effects.oneshot import EFFECT_MAP

AUDIO_DIR = "audio_library"
CHUNK = 1024


class SharedState:
    def __init__(self, custom_labels):
        self.seek_position = 0.0
        self.user_seek_active = False
        self.clicked_button = None
        self.current_track_name = ""
        self.is_paused = True  # Start paused
        self.custom_labels = custom_labels
        self.active_effect = None
        self.in_effect = False
        self.effect_start_time = 0.0
        self.edit_mode = False


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
    visualizer = LEDVisualizer(state, cfg_path)

    running = True
    while running:
        clicked, seek_drag = visualizer.handle_events()

        if clicked:
            if clicked == "edit":
                state.edit_mode = not state.edit_mode
                state.is_paused = True
                print(f"[INFO] Edit mode {'enabled' if state.edit_mode else 'disabled'}")

            elif clicked == "save" and state.edit_mode and visualizer.dirty:
                visualizer.save_config()
                print("[INFO] Changes saved")
                state.edit_mode = False
                visualizer.dirty = False

            elif clicked == "exit":
                running = False
                break

            elif clicked in EFFECT_MAP and not state.edit_mode:
                state.active_effect = clicked
                state.in_effect = True
                state.effect_start_time = time.time()
                print(f"[EFFECT] Starting effect: {clicked}")

            elif not state.in_effect and not state.edit_mode:
                state.clicked_button = clicked


        # Playback controls
        action = state.clicked_button
        state.clicked_button = None

        if action == "pause":
            state.is_paused = not state.is_paused
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
            if not state.is_paused:
                start_audio(position)

        elif action == "prev":
            index = (index - 1) % len(playlist)
            samples, sr = load_audio(playlist[index])
            eq = Equalizer10Band(sr)
            position = 0
            state.current_track_name = playlist[index]
            if not state.is_paused:
                start_audio(position)

        if seek_drag and not state.edit_mode:
            mx = pygame.mouse.get_pos()[0]
            r = visualizer.slider_rect
            if r and r.collidepoint(mx, r.y):
                state.seek_position = (mx - r.x) / r.width
                position = int(state.seek_position * len(samples))
                print(f"[SEEK] Jumped to {state.seek_position:.2%}")
                if not state.is_paused:
                    start_audio(position)

        # EFFECTS or AUDIO VISUALIZATION
        if state.in_effect and state.active_effect:
            elapsed = time.time() - state.effect_start_time
            effect_fn = EFFECT_MAP.get(state.active_effect)
            if effect_fn:
                colors, done = effect_fn(visualizer.leds, elapsed)
                visualizer.update_leds(colors)
                if done:
                    print(f"[EFFECT] Finished: {state.active_effect}")
                    state.in_effect = False
                    state.active_effect = None

        elif not state.is_paused and position + CHUNK < len(samples):
            chunk = samples[position:position + CHUNK].astype(np.float32)
            bands = eq.process(chunk)
            colors = blended_eq_pattern(bands, len(visualizer.leds))
            position += CHUNK
            visualizer.update_leds(colors)

        else:
            visualizer.update_leds([(0, 0, 0)] * len(visualizer.leds))

        state.seek_position = position / len(samples)
        visualizer.draw()
        time.sleep(CHUNK / sr)

    if playback:
        playback.stop()
    pygame.quit()
    print("[INFO] Program exited cleanly.")


if __name__ == "__main__":
    main()
