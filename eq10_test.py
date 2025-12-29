import wave
import numpy as np
from simulator.audio.equalizer import Equalizer10Band

wav = wave.open("example_audio/test.wav", "rb")
sample_rate = wav.getframerate()
frames = wav.readframes(1024)
samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

eq = Equalizer10Band(sample_rate)
bands = eq.process(samples)

for i, val in enumerate(bands):
    print(f"Band {i}: {val:.2f}")
