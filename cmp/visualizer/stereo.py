"""Stereo spectrum visualizer - displays left and right channels separately."""
import numpy as np
from typing import List, Tuple
from .base import BaseVisualizer


class StereoVisualizer(BaseVisualizer):
    """Stereo spectrum with left and right channels displayed side by side."""
    
    def __init__(self, bar_count: int = 16, smoothing: float = 0.3, sensitivity: float = 1.0):
        # Each channel gets half the bars
        super().__init__(bar_count * 2, smoothing)
        self.channel_bars = bar_count
        self.sensitivity = sensitivity
        self.fft_size = 2048
        self._window = np.hanning(self.fft_size)
        self._previous_left = np.zeros(bar_count)
        self._previous_right = np.zeros(bar_count)
    
    @property
    def name(self) -> str:
        return "stereo"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process stereo audio data, returns combined left+right data."""
        # Split into left and right channels
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
        else:
            # Mono - duplicate to both channels
            left = audio_data
            right = audio_data
        
        # Ensure enough samples
        if len(left) < self.fft_size:
            left = np.pad(left, (0, self.fft_size - len(left)))
            right = np.pad(right, (0, self.fft_size - len(right)))
        else:
            left = left[:self.fft_size]
            right = right[:self.fft_size]
        
        # Process each channel
        left_values = self._process_channel(left, self._previous_left)
        right_values = self._process_channel(right, self._previous_right)
        
        self._previous_left = left_values.copy()
        self._previous_right = right_values.copy()
        
        # Combine: left values followed by right values
        return np.concatenate([left_values, right_values])
    
    def _process_channel(self, audio_data: np.ndarray, previous: np.ndarray) -> np.ndarray:
        """Process single channel."""
        # Apply window
        audio_data = audio_data * self._window
        
        # FFT
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        # Create frequency bins
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / 44100)  # Assuming 44.1kHz
        
        # Log-spaced bins
        min_freq = 20
        max_freq = freqs[-1] if len(freqs) > 0 else 20000
        
        log_bins = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            self.channel_bars + 1
        )
        
        # Convert to indices
        bins = []
        for freq in log_bins:
            idx = np.searchsorted(freqs, freq)
            idx = min(idx, len(freqs) - 1)
            bins.append(idx)
        
        # Aggregate magnitudes
        values = np.zeros(self.channel_bars)
        for i in range(self.channel_bars):
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
        values = self.smoothing * previous + (1 - self.smoothing) * values
        
        return values
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render stereo spectrum with left and right channels."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Split data into left and right
        mid = len(data) // 2
        left_data = data[:mid]
        right_data = data[mid:]
        
        # Calculate widths
        gap = 4  # Gap between channels
        label_width = 2  # "L " and " R"
        available_width = width - gap - (label_width * 2)
        channel_width = available_width // 2
        
        lines = []
        
        # Build each row from top to bottom
        for row in range(height):
            threshold = 1.0 - (row / height)
            
            # Left channel (reversed for visual effect - bass on outside)
            left_line = "L "
            for value in reversed(left_data[:channel_width]):
                if value >= threshold:
                    bar_intensity = min(1.0, (value - threshold) * height)
                    left_line += self.value_to_bar(bar_intensity)
                else:
                    left_line += " "
            
            # Ensure exact width
            left_line = left_line[:label_width + channel_width].ljust(label_width + channel_width)
            
            # Gap
            middle_gap = " " * gap
            
            # Right channel
            right_line = ""
            for value in right_data[:channel_width]:
                if value >= threshold:
                    bar_intensity = min(1.0, (value - threshold) * height)
                    right_line += self.value_to_bar(bar_intensity)
                else:
                    right_line += " "
            right_line = right_line[:channel_width]
            right_line += " R"
            
            # Combine
            full_line = left_line + middle_gap + right_line
            full_line = full_line[:width].ljust(width)
            lines.append(full_line)
        
        return lines


class StereoWaveformVisualizer(BaseVisualizer):
    """Stereo waveform display - left and right channels as waveforms."""
    
    def __init__(self, smoothing: float = 0.2):
        super().__init__(bar_count=0, smoothing=smoothing)
        self._previous_left = np.zeros(128)
        self._previous_right = np.zeros(128)
    
    @property
    def name(self) -> str:
        return "stereo_waveform"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process stereo audio data."""
        target_size = 64  # Each channel gets 64 samples
        
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
        else:
            left = audio_data
            right = audio_data
        
        # Resample
        if len(left) != target_size:
            indices = np.linspace(0, len(left) - 1, target_size, dtype=int)
            left = left[indices]
        if len(right) != target_size:
            indices = np.linspace(0, len(right) - 1, target_size, dtype=int)
            right = right[indices]
        
        # Normalize
        max_left = np.max(np.abs(left))
        max_right = np.max(np.abs(right))
        
        if max_left > 0:
            left = left / max_left
        if max_right > 0:
            right = right / max_right
        
        # Smooth
        left = self.smoothing * self._previous_left + (1 - self.smoothing) * left
        right = self.smoothing * self._previous_right + (1 - self.smoothing) * right
        
        self._previous_left = left.copy()
        self._previous_right = right.copy()
        
        # Interleave left and right: L0, R0, L1, R1, ...
        result = np.zeros(target_size * 2)
        result[0::2] = left
        result[1::2] = right
        
        return result
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render stereo waveform."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Split interleaved data
        left = data[0::2]
        right = data[1::2]
        
        half_height = height // 2
        
        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        # Resample to fit width
        if len(left) * 2 != width:
            indices = np.linspace(0, len(left) - 1, width // 2, dtype=int)
            left = left[indices]
            right = right[indices]
        
        # Draw center line
        center = half_height
        for x in range(width):
            canvas[center][x] = "·"
        
        # Draw left channel (top half)
        for i, value in enumerate(left):
            x = i * 2
            if x >= width:
                break
            y = int(center - abs(value) * (half_height - 1))
            y = max(0, min(y, center - 1))
            
            # Draw from center up to y
            for py in range(y, center):
                char = "│" if py == y else "│"
                canvas[py][x] = char
        
        # Draw right channel (bottom half)
        for i, value in enumerate(right):
            x = i * 2 + 1
            if x >= width:
                break
            y = int(center + abs(value) * (half_height - 1))
            y = min(height - 1, max(center + 1, y))
            
            # Draw from center down to y
            for py in range(center + 1, y + 1):
                char = "│" if py == y else "│"
                canvas[py][x] = char
        
        lines = ["".join(row) for row in canvas]
        return lines
