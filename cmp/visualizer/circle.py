"""Circular/Radial spectrum visualizer."""
import numpy as np
from typing import List
from .base import BaseVisualizer


class CircleVisualizer(BaseVisualizer):
    """Circular spectrum analyzer with energy radiating from center."""
    
    # Characters for different energy levels (from low to high)
    CIRCLE_CHARS = ["·", "∘", "○", "◯", "●", "◐", "◑"]
    
    def __init__(self, bar_count: int = 32, smoothing: float = 0.3, sensitivity: float = 1.0):
        super().__init__(bar_count, smoothing)
        self.sensitivity = sensitivity
        self.fft_size = 2048
        self._window = np.hanning(self.fft_size)
        self._rotation_offset = 0
    
    @property
    def name(self) -> str:
        return "circle"
    
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
        
        # Create log-spaced bins for radial display
        bins = self._create_radial_bins(freqs)
        
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
    
    def _create_radial_bins(self, freqs: np.ndarray) -> List[int]:
        """Create logarithmically spaced frequency bins for radial display."""
        # Frequency range: 20Hz to Nyquist
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
        """Render circular spectrum."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Use square area, centered
        size = min(width, height * 2)  # *2 because chars are taller than wide
        radius = size // 4
        
        # Center position
        cx = width // 2
        cy = height // 2
        
        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        # Draw circular spectrum
        num_bars = len(data)
        for i, value in enumerate(data):
            # Calculate angle (start from top, go clockwise)
            angle = 2 * np.pi * i / num_bars - np.pi / 2
            
            # Calculate bar length based on value
            bar_length = int(value * radius * 0.8)
            
            # Draw bar from inner radius to outer
            inner_r = radius // 3
            for r in range(inner_r, inner_r + bar_length):
                x = int(cx + r * np.cos(angle))
                y = int(cy + r * np.sin(angle) / 2)  # /2 for aspect ratio correction
                
                if 0 <= x < width and 0 <= y < height:
                    # Choose character based on distance (energy level)
                    char_idx = min(int((r - inner_r) / bar_length * len(self.CIRCLE_CHARS)), 
                                   len(self.CIRCLE_CHARS) - 1) if bar_length > 0 else 0
                    canvas[y][x] = self.CIRCLE_CHARS[char_idx]
        
        # Convert canvas to strings
        lines = []
        for row in canvas:
            lines.append("".join(row))
        
        return lines


class RadialVisualizer(CircleVisualizer):
    """Alternative radial visualizer with different rendering style."""
    
    RADIAL_CHARS = ["░", "▒", "▓", "█"]
    
    @property
    def name(self) -> str:
        return "radial"
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render radial spectrum with filled sectors."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        cx = width // 2
        cy = height // 2
        max_radius = min(cx, cy * 2) - 1
        
        num_bars = len(data)
        
        # Draw filled radial bars
        for r in range(max_radius, 0, -1):
            for angle_idx, value in enumerate(data):
                # Map value to radius threshold
                threshold_radius = int(value * max_radius * 0.9)
                
                if r > threshold_radius:
                    continue
                
                # Calculate angle range for this bar
                start_angle = 2 * np.pi * angle_idx / num_bars - np.pi / 2
                end_angle = 2 * np.pi * (angle_idx + 1) / num_bars - np.pi / 2
                
                # Draw arc segment
                num_steps = max(1, int(r * (end_angle - start_angle)))
                for step in range(num_steps):
                    angle = start_angle + (end_angle - start_angle) * step / num_steps
                    x = int(cx + r * np.cos(angle))
                    y = int(cy + r * np.sin(angle) / 2)
                    
                    if 0 <= x < width and 0 <= y < height:
                        # Choose character based on radius
                        char_idx = min(r // (max_radius // len(self.RADIAL_CHARS) + 1), 
                                       len(self.RADIAL_CHARS) - 1)
                        canvas[y][x] = self.RADIAL_CHARS[char_idx]
        
        lines = ["".join(row) for row in canvas]
        return lines
