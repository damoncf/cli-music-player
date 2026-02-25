"""Visualizer widget."""
from textual.widgets import Static
from textual.reactive import reactive
import numpy as np
from typing import Optional

from ...visualizer.manager import visualizer_manager


class VisualizerWidget(Static):
    """Audio visualization widget using the visualizer manager."""
    
    enabled = reactive(True)
    visualizer_type = reactive("spectrum")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        if self._audio_data is None or not self.enabled:
            self.update("")
            return
        
        width = self.size.width if self.size else 40
        height = self.size.height if self.size else 8
        
        try:
            # Use the visualizer manager to process and render
            visualizer = visualizer_manager.current
            if visualizer:
                data = visualizer.process(self._audio_data)
                lines = visualizer.render(data, width, height)
                content = "\n".join(lines[:height])
                self.update(content)
            else:
                self.update("")
        except Exception:
            self.update("")
    
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
        visualizer_manager.switch_to(vtype)
