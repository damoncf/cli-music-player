"""Visualizer widget."""
from textual.widgets import Static
from textual.reactive import reactive
from textual.color import Color
import numpy as np
from typing import Optional
from ...visualizer.spectrum import SpectrumVisualizer, CompactSpectrumVisualizer
from ...visualizer.waveform import SimpleWaveformVisualizer


class VisualizerWidget(Static):
    """Audio visualization widget."""
    
    enabled = reactive(True)
    visualizer_type = reactive("spectrum")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spectrum = SpectrumVisualizer(bar_count=32, smoothing=0.3)
        self._compact_spectrum = CompactSpectrumVisualizer(bar_count=64, smoothing=0.3)
        self._waveform = SimpleWaveformVisualizer(smoothing=0.3)
        self._audio_data: Optional[np.ndarray] = None
        self._color = "#00ff00"
        self._bg_color = "#000000"
    
    def set_colors(self, primary: str, background: str):
        """Set visualizer colors."""
        self._color = primary
        self._bg_color = background
    
    def update_audio_data(self, data: np.ndarray):
        """Update audio data for visualization."""
        self._audio_data = data
        if self.enabled:
            self.refresh_visualization()
    
    def refresh_visualization(self):
        """Refresh the visualization display."""
        if self._audio_data is None:
            self.update("")
            return
        
        width = self.size.width if self.size else 40
        height = self.size.height if self.size else 8
        
        try:
            if self.visualizer_type == "spectrum":
                data = self._spectrum.process(self._audio_data)
                lines = self._spectrum.render(data, width, height)
            elif self.visualizer_type == "waveform":
                data = self._waveform.process(self._audio_data)
                lines = self._waveform.render(data, width, height)
            else:
                data = self._compact_spectrum.process(self._audio_data)
                lines = self._compact_spectrum.render(data, width, 1)
            
            content = "\n".join(lines[:height])
            self.update(content)
        except Exception:
            pass
    
    def watch_enabled(self, enabled: bool):
        """Handle enabled state change."""
        if not enabled:
            self.update("")
    
    def on_mount(self):
        """Initialize on mount."""
        self.set_interval(1/30, self.refresh_visualization)
    
    def set_type(self, vtype: str):
        """Set visualizer type."""
        self.visualizer_type = vtype
