# simulator/audio/equalizer.py

import numpy as np

class Equalizer10Band:
    def __init__(self, sample_rate: int, fft_size: int = 1024):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.freqs = np.fft.rfftfreq(fft_size, d=1.0 / sample_rate)

        # Define 10 logarithmic bands (frequencies in Hz)
        self.bands = [
            (20, 40),
            (40, 80),
            (80, 160),
            (160, 315),
            (315, 630),
            (630, 1250),
            (1250, 2500),
            (2500, 5000),
            (5000, 10000),
            (10000, 20000)
        ]

    def _band_energy(self, spectrum, band):
        low, high = band
        idx = np.where((self.freqs >= low) & (self.freqs < high))[0]
        if len(idx) == 0:
            return 0.0
        return np.mean(spectrum[idx])

    def process(self, samples: np.ndarray):
        if len(samples) < self.fft_size:
            samples = np.pad(samples, (0, self.fft_size - len(samples)))

        samples = samples[:self.fft_size]
        window = np.hanning(len(samples))
        samples = samples * window
        spectrum = np.abs(np.fft.rfft(samples))

        # Compute band energies
        energies = [self._band_energy(spectrum, band) for band in self.bands]

        # Normalize (max of all bands to 1.0)
        max_energy = max(max(energies), 1e-6)
        normalized = [e / max_energy for e in energies]

        return normalized  # List of 10 floats [0.0–1.0]
