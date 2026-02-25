"""Compact layout - minimal view for small terminals."""
from typing import List
from textual.containers import Container, Horizontal
from textual.widgets import Label, Footer

from .base import Layout
from ..widgets.progress_bar import ProgressBar
from ..widgets.volume_bar import VolumeBar
from ..widgets.playlist_widget import PlaylistWidget


class CompactLayout(Layout):
    """Compact layout for small terminals."""
    
    name = "compact"
    display_name = "Compact"
    description = "Minimal view without visualizer, optimized for small terminals"
    
    @property
    def min_height(self) -> int:
        return 5
    
    @property
    def min_width(self) -> int:
        return 40
    
    def compose(self, screen) -> List:
        """Compose the compact layout."""
        from ...themes.manager import theme_manager
        theme = theme_manager.current
        
        widgets = []
        
        # Header - single line with title, track, and time
        header = Container(
            Horizontal(
                Label("CMP ♪", id="app-title"),
                Label("No track", id="now-playing", classes="compact-track"),
                Label("00:00", id="time-display"),
                classes="compact-header"
            ),
            classes="header compact"
        )
        widgets.append(header)
        
        # Progress bar only
        screen.progress_bar = ProgressBar(classes="progress-bar compact")
        screen.progress_bar.set_chars(
            theme.chars.progress_filled,
            theme.chars.progress_empty
        )
        progress_container = Container(screen.progress_bar, classes="progress-container compact")
        widgets.append(progress_container)
        
        # Compact controls - single row
        screen.volume_bar = VolumeBar(classes="volume-bar compact")
        screen.volume_bar.set_chars(
            "█", "░", "M"
        )
        
        controls = Horizontal(
            Label(theme.chars.prev, id="btn-prev"),
            Label(theme.chars.play, id="btn-play"),
            Label(theme.chars.next, id="btn-next"),
            Label(" ", id="shuffle-indicator"),  # Compact shuffle indicator
            Label(" ", id="repeat-indicator"),   # Compact repeat indicator
            screen.volume_bar,
            classes="controls-container compact"
        )
        widgets.append(controls)
        
        # Compact playlist - single line scrolling (hidden by default)
        screen.playlist_widget = PlaylistWidget(
            screen.playlist,
            classes="playlist compact"
        )
        screen.playlist_widget.set_colors(
            theme.colors.playlist_current,
            theme.colors.playlist_selected
        )
        screen.playlist_widget.display = False
        playlist_container = Container(screen.playlist_widget, classes="playlist-container compact")
        widgets.append(playlist_container)
        
        # Single line status
        status_bar = Horizontal(
            Label("Ready", id="status-text"),
            classes="status-bar compact"
        )
        widgets.append(status_bar)
        
        return widgets
