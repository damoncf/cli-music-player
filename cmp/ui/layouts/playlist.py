"""Playlist layout - maximizes playlist area."""
from typing import List
from textual.containers import Container, Horizontal
from textual.widgets import Label, Footer, Static

from .base import Layout
from ..widgets.progress_bar import ProgressBar
from ..widgets.volume_bar import VolumeBar
from ..widgets.playlist_widget import PlaylistWidget


class PlaylistLayout(Layout):
    """Playlist-first layout for managing large music libraries."""
    
    name = "playlist"
    display_name = "Playlist"
    description = "Maximizes playlist view for easy track selection"
    
    @property
    def min_height(self) -> int:
        return 15
    
    @property
    def min_width(self) -> int:
        return 70
    
    def compose(self, screen) -> List:
        """Compose the playlist layout."""
        from ...themes.manager import theme_manager
        theme = theme_manager.current
        
        widgets = []
        
        # Compact header
        header = Container(
            Label("CMP - CLI Music Player", id="app-title"),
            classes="header minimal"
        )
        widgets.append(header)
        
        # Large playlist area with column headers
        playlist_header = Horizontal(
            Label("#", classes="col-num"),
            Label("Title", classes="col-title"),
            Label("Artist", classes="col-artist"),
            Label("Duration", classes="col-duration"),
            classes="playlist-header"
        )
        
        screen.playlist_widget = PlaylistWidget(
            screen.playlist,
            classes="playlist large"
        )
        screen.playlist_widget.set_colors(
            theme.colors.playlist_current,
            theme.colors.playlist_selected
        )
        # Show playlist by default in this layout
        screen.playlist_widget.display = True
        screen.show_playlist = True
        
        playlist_section = Container(
            playlist_header,
            screen.playlist_widget,
            classes="playlist-section"
        )
        widgets.append(playlist_section)
        
        # Progress bar
        screen.progress_bar = ProgressBar(classes="progress-bar")
        screen.progress_bar.set_chars(
            theme.chars.progress_filled,
            theme.chars.progress_empty
        )
        progress_container = Container(screen.progress_bar, classes="progress-container")
        widgets.append(progress_container)
        
        # Controls with current track info
        screen.volume_bar = VolumeBar(classes="volume-bar")
        screen.volume_bar.set_chars(
            theme.chars.volume_filled,
            theme.chars.volume_empty,
            "🔇"
        )
        
        controls = Horizontal(
            Label(theme.chars.prev, id="btn-prev"),
            Label(f"[ {theme.chars.play} ]", id="btn-play"),
            Label(theme.chars.next, id="btn-next"),
            Label("No track loaded", id="now-playing", classes="playlist-layout-track"),
            Label("00:00 / 00:00", id="time-display"),
            screen.volume_bar,
            classes="controls-container playlist-layout"
        )
        widgets.append(controls)
        
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
