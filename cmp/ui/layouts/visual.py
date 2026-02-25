"""Visual layout - maximizes the visualizer area."""
from typing import List
from textual.containers import Container, Horizontal
from textual.widgets import Label, Footer

from .base import Layout
from ..widgets.progress_bar import ProgressBar
from ..widgets.volume_bar import VolumeBar
from ..widgets.visualizer_widget import VisualizerWidget
from ..widgets.playlist_widget import PlaylistWidget


class VisualLayout(Layout):
    """Visual-first layout with large visualizer area."""
    
    name = "visual"
    display_name = "Visual"
    description = "Maximizes the visualizer for an immersive experience"
    
    @property
    def min_height(self) -> int:
        return 18
    
    @property
    def min_width(self) -> int:
        return 60
    
    def compose(self, screen) -> List:
        """Compose the visual layout."""
        from ...themes.manager import theme_manager
        theme = theme_manager.current
        
        widgets = []
        
        # Large visualizer area (15 rows)
        screen.visualizer = VisualizerWidget(classes="visualizer large")
        screen.visualizer.set_colors(
            theme.colors.visualizer_primary,
            theme.colors.background
        )
        viz_container = Container(screen.visualizer, classes="visualizer-container large")
        widgets.append(viz_container)
        
        # Progress bar
        screen.progress_bar = ProgressBar(classes="progress-bar")
        screen.progress_bar.set_chars(
            theme.chars.progress_filled,
            theme.chars.progress_empty
        )
        progress_container = Container(screen.progress_bar, classes="progress-container")
        widgets.append(progress_container)
        
        # Info and controls in one row
        screen.volume_bar = VolumeBar(classes="volume-bar")
        screen.volume_bar.set_chars(
            theme.chars.volume_filled,
            theme.chars.volume_empty,
            "🔇"
        )
        
        info_controls = Horizontal(
            Label(theme.chars.prev, id="btn-prev"),
            Label(f"[ {theme.chars.play} ]", id="btn-play"),
            Label(theme.chars.next, id="btn-next"),
            Label("No track loaded", id="now-playing", classes="visual-layout-track"),
            Label("00:00 / 00:00", id="time-display"),
            screen.volume_bar,
            classes="controls-container visual-layout"
        )
        widgets.append(info_controls)
        
        # Playlist (hidden by default)
        screen.playlist_widget = PlaylistWidget(
            screen.playlist,
            classes="playlist"
        )
        screen.playlist_widget.set_colors(
            theme.colors.playlist_current,
            theme.colors.playlist_selected
        )
        screen.playlist_widget.display = False
        playlist_container = Container(screen.playlist_widget, classes="playlist-container")
        widgets.append(playlist_container)
        
        # Minimal status bar
        status_bar = Horizontal(
            Label("CMP - Visual Mode", id="status-text"),
            classes="status-bar minimal"
        )
        widgets.append(status_bar)
        widgets.append(Footer())
        
        return widgets
