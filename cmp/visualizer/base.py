"""Base visualizer interface."""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class VisualizerPlugin(ABC):
    """Base class for visualizers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Visualizer name."""
        pass
    
    @abstractmethod
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data and return visualization data."""
        pass
    
    @abstractmethod
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render visualization to string lines."""
        pass


class BaseVisualizer:
    """Base visualizer with common utilities."""
    
    BARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    
    def __init__(self, bar_count: int = 32, smoothing: float = 0.3):
        self.bar_count = bar_count
        self.smoothing = smoothing
        self._previous_data: np.ndarray = np.zeros(bar_count)
    
    def smooth(self, data: np.ndarray) -> np.ndarray:
        """Apply smoothing to data."""
        smoothed = self.smoothing * self._previous_data + (1 - self.smoothing) * data
        self._previous_data = smoothed
        return smoothed
    
    def value_to_bar(self, value: float) -> str:
        """Convert value (0-1) to bar character."""
        idx = int(value * (len(self.BARS) - 1))
        idx = max(0, min(idx, len(self.BARS) - 1))
        return self.BARS[idx]
