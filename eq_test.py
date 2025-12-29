import sys
import os

# Add the project root to the import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import wave
import numpy as np
from simulator.audio.equalizer import Equalizer

wav = wave.open("example_audio/test.wav", "rb")

sample_rate = wav.getframerate()
frames = wav.readframes(1024)
samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

eq = Equalizer(sample_rate)
bands = eq.process(samples)

print(bands)
