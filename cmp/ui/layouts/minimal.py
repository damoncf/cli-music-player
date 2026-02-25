"""Minimal layout - single line display."""
from typing import List
from textual.containers import Horizontal
from textual.widgets import Label

from .base import Layout


class MinimalLayout(Layout):
    """Minimal single-line layout for background playback."""
    
    name = "minimal"
    display_name = "Minimal"
    description = "Single line display, perfect for background playback"
    
    @property
    def min_height(self) -> int:
        return 1
    
    @property
    def min_width(self) -> int:
        return 40
    
    def compose(self, screen) -> List:
        """Compose the minimal layout."""
        from ...themes.manager import theme_manager
        theme = theme_manager.current
        
        widgets = []
        
        # Single line with all info
        screen.playlist_widget = None  # No playlist in minimal mode
        screen.visualizer = None  # No visualizer
        screen.progress_bar = None  # No progress bar
        screen.volume_bar = None  # No volume bar
        
        minimal_bar = Horizontal(
            Label("♪", id="app-title"),
            Label("▶", id="btn-play"),
            Label("No track", id="now-playing", classes="minimal-track"),
            Label("00:00", id="time-display"),
            classes="minimal-container"
        )
        widgets.append(minimal_bar)
        
        return widgets
