
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio as play

# Load a test .wav file
audio = AudioSegment.from_wav("example_audio/test.wav")  # <-- Make sure this file exists
play(audio)