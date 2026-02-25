"""Main TUI application."""
from textual.app import App, ComposeResult
from textual.binding import Binding

from ..player.engine import audio_engine
from ..player.playlist import Playlist
from ..config.settings import config_manager

from .screens.player_screen import PlayerScreen


class MusicPlayerApp(App):
    """Main music player application."""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    /* Header styles */
    .header {
        height: 3;
        dock: top;
        padding: 0 1;
    }
    .header.compact {
        height: 1;
    }
    .header.minimal {
        height: 1;
    }
    
    #app-title {
        text-style: bold;
        color: $primary;
    }
    #now-playing {
        text-align: center;
        text-style: bold;
    }
    #time-display {
        text-align: right;
    }
    .compact-track {
        width: 1fr;
        text-align: center;
    }
    .visual-layout-track {
        width: 1fr;
        text-align: center;
    }
    .playlist-layout-track {
        width: 1fr;
        text-align: center;
    }
    .minimal-track {
        width: 1fr;
        text-align: center;
    }
    
    /* Visualizer styles */
    .visualizer-container {
        height: 10;
        padding: 0 2;
    }
    .visualizer-container.large {
        height: 15;
    }
    .visualizer-container.split {
        height: 100%;
    }
    .visualizer {
        height: 100%;
        content-align: center middle;
    }
    .visualizer.large {
        height: 100%;
    }
    
    /* Progress bar styles */
    .progress-container {
        height: 1;
        padding: 0 2;
    }
    .progress-container.compact {
        padding: 0 1;
    }
    .progress-bar {
        height: 100%;
    }
    .progress-bar.compact {
        height: 100%;
    }
    
    /* Controls styles */
    .controls-container {
        height: 3;
        padding: 0 2;
    }
    .controls-container.compact {
        height: 1;
        padding: 0 1;
    }
    .controls-container.visual-layout {
        height: 1;
    }
    .controls-container.playlist-layout {
        height: 1;
    }
    
    .playback-controls {
        width: 60%;
        content-align: center middle;
    }
    .playback-controls Label {
        padding: 0 1;
    }
    
    #btn-play {
        text-style: bold;
    }
    
    .volume-container {
        width: 40%;
        content-align: right middle;
    }
    .volume-bar {
        width: 100%;
    }
    .volume-bar.compact {
        width: 20;
    }
    
    /* Playlist styles */
    .playlist-section {
        height: 1fr;
        padding: 0 2;
    }
    .playlist-header {
        height: 1;
        padding: 0 1;
        text-style: bold;
        background: $primary 20%;
    }
    .col-num { width: 4; }
    .col-title { width: 1fr; }
    .col-artist { width: 1fr; }
    .col-duration { width: 10; }
    
    .playlist-container {
        height: 1fr;
        padding: 0 2;
    }
    .playlist-container.compact {
        height: 1;
        padding: 0 1;
    }
    .playlist {
        height: 100%;
        border: solid $primary;
    }
    .playlist.large {
        height: 100%;
        border: solid $primary;
    }
    .playlist.compact {
        height: 1;
        border: none;
    }
    
    /* Split layout styles */
    .split-container {
        height: 1fr;
    }
    .split-left {
        width: 60%;
        height: 100%;
    }
    .split-right {
        width: 40%;
        height: 100%;
    }
    
    /* Status bar styles */
    .status-bar {
        height: 1;
        dock: bottom;
        padding: 0 1;
    }
    .status-bar.compact {
        height: 1;
    }
    .status-bar.minimal {
        height: 1;
    }
    .status-bar Label {
        width: 1fr;
    }
    #status-text {
        text-align: left;
    }
    #status-volume {
        text-align: center;
    }
    #status-theme {
        text-align: right;
    }
    
    /* Minimal layout */
    .minimal-container {
        height: 1;
        content-align: center middle;
    }
    .minimal-container Label {
        padding: 0 1;
    }
    
    /* Compact header */
    .compact-header {
        height: 1;
        content-align: center middle;
    }
    .compact-header Label {
        padding: 0 1;
    }
    """
    
    def __init__(self, playlist: Playlist, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
    
    def on_mount(self):
        """Initialize on mount."""
        self.push_screen(PlayerScreen(self.playlist))
    
    def action_quit(self):
        """Quit the application."""
        self.exit()
    
    def on_unmount(self):
        """Cleanup on unmount."""
        audio_engine.shutdown()
        config_manager.save()
