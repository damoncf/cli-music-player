"""Waveform visualizer."""
import numpy as np
from typing import List
from .base import BaseVisualizer


class WaveformVisualizer(BaseVisualizer):
    """Time-domain waveform display."""
    
    def __init__(self, smoothing: float = 0.2):
        super().__init__(bar_count=0, smoothing=smoothing)
        self._previous_samples = np.zeros(1024)
    
    @property
    def name(self) -> str:
        return "waveform"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data - just normalize."""
        # Convert to mono
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Resample to fixed size
        target_size = 128
        if len(audio_data) != target_size:
            indices = np.linspace(0, len(audio_data) - 1, target_size, dtype=int)
            audio_data = audio_data[indices]
        
        # Normalize
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        # Smooth
        audio_data = self.smoothing * self._previous_samples + (1 - self.smoothing) * audio_data
        self._previous_samples = audio_data.copy()
        
        return audio_data
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render waveform."""
        if len(data) == 0:
            return [" " * width] * height
        
        lines = []
        center = height // 2
        
        # Resample data to fit width
        if len(data) != width:
            indices = np.linspace(0, len(data) - 1, width, dtype=int)
            data = data[indices]
        
        # Build each line
        for row in range(height):
            line = ""
            for value in data:
                # Map value (-1 to 1) to row position
                sample_row = int((1 - value) * (height - 1) / 2)
                
                if row == center:
                    line += "─"
                elif abs(row - center) <= abs(sample_row - center):
                    if row < center:
                        line += "│" if row == sample_row else "│"
                    else:
                        line += "│" if row == sample_row else "│"
                else:
                    line += " "
            lines.append(line)
        
        return lines


class SimpleWaveformVisualizer(BaseVisualizer):
    """Simple oscilloscope-style waveform."""
    
    WAVEFORM_CHARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]
    
    def __init__(self, smoothing: float = 0.3):
        super().__init__(smoothing=smoothing)
    
    @property
    def name(self) -> str:
        return "waveform_simple"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data."""
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Downsample
        target_size = 64
        if len(audio_data) > target_size:
            step = len(audio_data) // target_size
            audio_data = audio_data[::step][:target_size]
        
        # Normalize
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        return audio_data
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render simple waveform as single line."""
        if len(data) == 0:
            return [" " * width]
        
        # Map to characters
        chars = []
        for value in data[:width]:
            # Map -1..1 to 0..len(chars)-1
            idx = int((value + 1) / 2 * (len(self.WAVEFORM_CHARS) - 1))
            idx = max(0, min(idx, len(self.WAVEFORM_CHARS) - 1))
            chars.append(self.WAVEFORM_CHARS[idx])
        
        # Pad to width
        result = "".join(chars).ljust(width)
        return [result]
