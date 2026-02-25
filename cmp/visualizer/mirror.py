"""Mirror spectrum visualizer - symmetric display."""
import numpy as np
from typing import List
from .base import BaseVisualizer


class MirrorVisualizer(BaseVisualizer):
    """Mirror spectrum - symmetric display with warm colors on top, cool on bottom."""
    
    # Warm colors for top half
    WARM_CHARS = ["░", "▒", "▓", "█"]
    # Cool colors for bottom half  
    COOL_CHARS = ["░", "▒", "▓", "█"]
    
    def __init__(self, bar_count: int = 32, smoothing: float = 0.3, sensitivity: float = 1.0):
        super().__init__(bar_count, smoothing)
        self.sensitivity = sensitivity
        self.fft_size = 2048
        self._window = np.hanning(self.fft_size)
    
    @property
    def name(self) -> str:
        return "mirror"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data with FFT."""
        # Convert to mono
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Ensure enough samples
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)))
        else:
            audio_data = audio_data[:self.fft_size]
        
        # Apply window
        audio_data = audio_data * self._window
        
        # FFT
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        # Frequency bins
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / sample_rate)
        
        # Log-spaced bins
        min_freq = 20
        max_freq = freqs[-1] if len(freqs) > 0 else 20000
        
        log_bins = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            self.bar_count + 1
        )
        
        # Convert to indices
        bins = []
        for freq in log_bins:
            idx = np.searchsorted(freqs, freq)
            idx = min(idx, len(freqs) - 1)
            bins.append(idx)
        
        # Aggregate magnitudes
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
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render mirror spectrum."""
        if len(data) == 0:
            return [" " * width] * height
        
        lines = []
        half_height = height // 2
        bar_width = max(1, width // len(data))
        
        # Top half (mirrored - warm colors)
        for row in range(half_height):
            # Calculate threshold (higher row = higher threshold)
            threshold = 1.0 - (row / half_height)
            
            line = ""
            for value in data[:width // bar_width]:
                if value >= threshold:
                    # Map intensity to character
                    intensity = min(1.0, (value - threshold) * half_height)
                    char_idx = min(int(intensity * len(self.WARM_CHARS)), 
                                   len(self.WARM_CHARS) - 1)
                    line += self.WARM_CHARS[char_idx] * bar_width
                else:
                    line += " " * bar_width
            
            line = line[:width].ljust(width)
            lines.append(line)
        
        # Bottom half (normal - cool colors)
        for row in range(half_height):
            # Calculate threshold (lower row = higher threshold)
            threshold = row / half_height
            
            line = ""
            for value in data[:width // bar_width]:
                if value >= threshold:
                    intensity = min(1.0, (value - threshold) * half_height)
                    char_idx = min(int(intensity * len(self.COOL_CHARS)),
                                   len(self.COOL_CHARS) - 1)
                    line += self.COOL_CHARS[char_idx] * bar_width
                else:
                    line += " " * bar_width
            
            line = line[:width].ljust(width)
            lines.append(line)
        
        return lines


class SymmetryVisualizer(BaseVisualizer):
    """Symmetry visualizer - displays spectrum with center symmetry."""
    
    def __init__(self, bar_count: int = 32, smoothing: float = 0.3, sensitivity: float = 1.0):
        # Half the bars since we'll mirror
        super().__init__(bar_count // 2, smoothing)
        self.sensitivity = sensitivity
        self.fft_size = 2048
        self._window = np.hanning(self.fft_size)
        self.display_bars = bar_count
    
    @property
    def name(self) -> str:
        return "symmetry"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data - same as spectrum."""
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)))
        else:
            audio_data = audio_data[:self.fft_size]
        
        audio_data = audio_data * self._window
        
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / sample_rate)
        
        min_freq = 20
        max_freq = freqs[-1] if len(freqs) > 0 else 20000
        
        log_bins = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            self.bar_count + 1
        )
        
        bins = []
        for freq in log_bins:
            idx = np.searchsorted(freqs, freq)
            idx = min(idx, len(freqs) - 1)
            bins.append(idx)
        
        values = np.zeros(self.bar_count)
        for i in range(self.bar_count):
            start_idx, end_idx = bins[i], bins[i + 1]
            if end_idx > start_idx:
                values[i] = np.mean(magnitude[start_idx:end_idx])
        
        max_val = np.max(values)
        if max_val > 0:
            values = values / max_val
        
        values = np.power(values, 1.0 / self.sensitivity)
        values = np.clip(values, 0, 1)
        
        values = self.smooth(values)
        
        # Create symmetric output: reverse + original
        return np.concatenate([values[::-1], values])
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render symmetric spectrum."""
        if len(data) == 0:
            return [" " * width] * height
        
        lines = []
        bar_width = max(1, width // len(data))
        
        for row in range(height):
            threshold = 1.0 - (row / height)
            
            line = ""
            for i, value in enumerate(data[:width // bar_width]):
                if value >= threshold:
                    # Center bars are "warmer" (denser chars)
                    center_dist = abs(i - len(data) / 2) / (len(data) / 2)
                    if center_dist < 0.3:
                        chars = ["▓", "█"]
                    elif center_dist < 0.7:
                        chars = ["▒", "▓"]
                    else:
                        chars = ["░", "▒"]
                    
                    intensity = min(1.0, (value - threshold) * height)
                    char_idx = min(int(intensity * len(chars)), len(chars) - 1)
                    line += chars[char_idx] * bar_width
                else:
                    line += " " * bar_width
            
            line = line[:width].ljust(width)
            lines.append(line)
        
        return lines
