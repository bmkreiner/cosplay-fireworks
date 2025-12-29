import simpleaudio as sa

class AudioPlayer:
    def __init__(self, filepath):
        print(f"[AudioPlayer] Loading WAV file: {filepath}")
        self.wave = sa.WaveObject.from_wave_file(filepath)

    def play(self):
        print("[AudioPlayer] Playing...")
        play_obj = self.wave.play()
        play_obj.wait_done()   # 🔑 THIS IS THE IMPORTANT LINE
        print("[AudioPlayer] Done.")
