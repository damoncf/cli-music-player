"""Spectrum analyzer visualizer."""
import numpy as np
from typing import List
from .base import BaseVisualizer


class SpectrumVisualizer(BaseVisualizer):
    """FFT spectrum analyzer."""
    
    def __init__(self, bar_count: int = 32, smoothing: float = 0.3, 
                 sensitivity: float = 1.0):
        super().__init__(bar_count, smoothing)
        self.sensitivity = sensitivity
        self.fft_size = 2048
        self._window = np.hanning(self.fft_size)
    
    @property
    def name(self) -> str:
        return "spectrum"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data with FFT."""
        # Convert to mono if stereo
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Ensure we have enough samples
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)))
        else:
            audio_data = audio_data[:self.fft_size]
        
        # Apply window function
        audio_data = audio_data * self._window
        
        # FFT
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        # Convert to frequency bins (log scale)
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / sample_rate)
        
        # Create log-spaced bins
        bins = self._create_log_bins(freqs)
        
        # Aggregate magnitudes into bins
        values = np.zeros(self.bar_count)
        for i in range(self.bar_count):
            start_idx, end_idx = bins[i], bins[i + 1]
            if end_idx > start_idx:
                values[i] = np.mean(magnitude[start_idx:end_idx])
        
        # Normalize
        max_val = np.max(values)
        if max_val > 0:
            values = values / max_val
        
        # Apply sensitivity
        values = np.power(values, 1.0 / self.sensitivity)
        values = np.clip(values, 0, 1)
        
        # Smooth
        values = self.smooth(values)
        
        return values
    
    def _create_log_bins(self, freqs: np.ndarray) -> List[int]:
        """Create logarithmically spaced frequency bins."""
        # Frequency range: 20Hz to Nyquist (sample_rate/2)
        min_freq = 20
        max_freq = freqs[-1] if len(freqs) > 0 else 20000
        
        log_bins = np.logspace(
            np.log10(min_freq), 
            np.log10(max_freq), 
            self.bar_count + 1
        )
        
        # Convert frequencies to indices
        bins = []
        for freq in log_bins:
            idx = np.searchsorted(freqs, freq)
            idx = min(idx, len(freqs) - 1)
            bins.append(idx)
        
        return bins
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render spectrum as bar chart."""
        if len(data) == 0:
            return [" " * width] * height
        
        lines = []
        bar_width = max(1, width // len(data))
        
        # Create each row from top to bottom
        for row in range(height):
            threshold = 1.0 - (row / height)
            line = ""
            for value in data[:width // bar_width]:
                if value >= threshold:
                    line += self.value_to_bar(min(1.0, (value - threshold) * height)) * bar_width
                else:
                    line += " " * bar_width
            # Pad to width
            line = line[:width].ljust(width)
            lines.append(line)
        
        return lines


class CompactSpectrumVisualizer(SpectrumVisualizer):
    """Compact single-line spectrum."""
    
    def render(self, data: np.ndarray, width: int, height: int = 1) -> List[str]:
        """Render compact spectrum."""
        if len(data) == 0:
            return [" " * width]
        
        # Sample data to fit width
        samples_needed = min(width, len(data))
        indices = np.linspace(0, len(data) - 1, samples_needed, dtype=int)
        sampled = data[indices]
        
        line = ""
        for value in sampled:
            line += self.value_to_bar(value)
        
        return [line.ljust(width)]
