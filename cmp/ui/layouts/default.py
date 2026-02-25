"""Default layout - balanced view with all components."""
from typing import List
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Footer

from .base import Layout
from ..widgets.progress_bar import ProgressBar
from ..widgets.volume_bar import VolumeBar
from ..widgets.visualizer_widget import VisualizerWidget
from ..widgets.playlist_widget import PlaylistWidget


class DefaultLayout(Layout):
    """Default balanced layout."""
    
    name = "default"
    display_name = "Default"
    description = "Balanced view with visualizer, controls, and playlist"
    
    @property
    def min_height(self) -> int:
        return 15
    
    @property
    def min_width(self) -> int:
        return 60
    
    def compose(self, screen) -> List:
        """Compose the default layout."""
        from ...themes.manager import theme_manager
        theme = theme_manager.current
        
        widgets = []
        
        # Header with now playing
        header = Container(
            Label("♪ CMP - CLI Music Player", id="app-title"),
            Label("No track loaded", id="now-playing"),
            Label("00:00 / 00:00", id="time-display"),
            classes="header"
        )
        widgets.append(header)
        
        # Visualizer
        screen.visualizer = VisualizerWidget(classes="visualizer")
        screen.visualizer.set_colors(
            theme.colors.visualizer_primary,
            theme.colors.background
        )
        viz_container = Container(screen.visualizer, classes="visualizer-container")
        widgets.append(viz_container)
        
        # Progress bar
        screen.progress_bar = ProgressBar(classes="progress-bar")
        screen.progress_bar.set_chars(
            theme.chars.progress_filled,
            theme.chars.progress_empty
        )
        progress_container = Container(screen.progress_bar, classes="progress-container")
        widgets.append(progress_container)
        
        # Controls
        screen.volume_bar = VolumeBar(classes="volume-bar")
        screen.volume_bar.set_chars(
            theme.chars.volume_filled,
            theme.chars.volume_empty,
            "🔇"
        )
        
        controls = Horizontal(
            Horizontal(
                Label(theme.chars.shuffle, id="shuffle-indicator"),
                Label(theme.chars.repeat, id="repeat-indicator"),
                Label(theme.chars.prev, id="btn-prev"),
                Label(f"[ {theme.chars.play} ]", id="btn-play"),
                Label(theme.chars.next, id="btn-next"),
                classes="playback-controls"
            ),
            Horizontal(
                screen.volume_bar,
                classes="volume-container"
            ),
            classes="controls-container"
        )
        widgets.append(controls)
        
        # Playlist (hidden by default)
        screen.playlist_widget = PlaylistWidget(
            screen.playlist,
            classes="playlist"
        )
        screen.playlist_widget.set_colors(
            theme.colors.playlist_current,
            theme.colors.playlist_selected
        )
        screen.playlist_widget.display = True
        playlist_container = Container(screen.playlist_widget, classes="playlist-container")
        widgets.append(playlist_container)
        
        # Status bar
        status_bar = Horizontal(
            Label("Ready", id="status-text"),
            Label("Vol: 70%", id="status-volume"),
            Label("Theme: default", id="status-theme"),
            classes="status-bar"
        )
        widgets.append(status_bar)
        widgets.append(Footer())
        
        return widgets
