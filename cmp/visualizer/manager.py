"""Visualizer manager for handling multiple visualizer types."""
from typing import Dict, List, Type, Optional
from .base import BaseVisualizer
from .spectrum import SpectrumVisualizer, CompactSpectrumVisualizer
from .waveform import WaveformVisualizer, SimpleWaveformVisualizer


class VisualizerManager:
    """Manages all available visualizers."""
    
    def __init__(self):
        self._visualizers: Dict[str, BaseVisualizer] = {}
        self._current: Optional[BaseVisualizer] = None
        self._current_name: str = "spectrum"
        self._register_builtin_visualizers()
    
    def _register_builtin_visualizers(self):
        """Register all built-in visualizers."""
        # Import here to avoid circular imports
        from .circle import CircleVisualizer
        from .stereo import StereoVisualizer
        from .mirror import MirrorVisualizer
        from .oscilloscope import OscilloscopeVisualizer
        
        visualizers = [
            SpectrumVisualizer(),
            CompactSpectrumVisualizer(),
            WaveformVisualizer(),
            SimpleWaveformVisualizer(),
            CircleVisualizer(),
            StereoVisualizer(),
            MirrorVisualizer(),
            OscilloscopeVisualizer(),
        ]
        
        for viz in visualizers:
            self._visualizers[viz.name] = viz
        
        # Set default
        self._current = self._visualizers.get("spectrum")
    
    def list_visualizers(self) -> List[str]:
        """List all available visualizer names."""
        return list(self._visualizers.keys())
    
    def get_visualizer(self, name: str) -> Optional[BaseVisualizer]:
        """Get visualizer by name."""
        return self._visualizers.get(name)
    
    @property
    def current(self) -> Optional[BaseVisualizer]:
        """Get current visualizer."""
        return self._current
    
    @property
    def current_name(self) -> str:
        """Get current visualizer name."""
        return self._current_name
    
    def switch_to(self, name: str) -> bool:
        """Switch to visualizer by name."""
        if name in self._visualizers:
            self._current = self._visualizers[name]
            self._current_name = name
            return True
        return False
    
    def next(self, reverse: bool = False) -> str:
        """Switch to next visualizer, returns new name."""
        names = self.list_visualizers()
        if not names:
            return self._current_name
        
        try:
            current_idx = names.index(self._current_name)
        except ValueError:
            current_idx = 0
        
        if reverse:
            next_idx = (current_idx - 1) % len(names)
        else:
            next_idx = (current_idx + 1) % len(names)
        
        new_name = names[next_idx]
        self.switch_to(new_name)
        return new_name
    
    def process(self, audio_data, sample_rate: int = 44100):
        """Process audio data with current visualizer."""
        if self._current:
            return self._current.process(audio_data, sample_rate)
        return None
    
    def render(self, data, width: int, height: int) -> List[str]:
        """Render with current visualizer."""
        if self._current:
            return self._current.render(data, width, height)
        return [" " * width] * height


# Global visualizer manager instance
visualizer_manager = VisualizerManager()
