"""Main TUI application."""
import sys
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Input
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen

from ..player.engine import audio_engine, PlaybackState, Track
from ..player.playlist import Playlist, RepeatMode
from ..player.metadata import format_duration, extract_metadata
from ..config.settings import config_manager
from ..themes.manager import theme_manager

from .widgets.progress_bar import ProgressBar
from .widgets.volume_bar import VolumeBar
from .widgets.visualizer_widget import VisualizerWidget
from .widgets.playlist_widget import PlaylistWidget


class PlayerScreen(Screen):
    """Main player screen."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "play_pause", "Play/Pause"),
        Binding("n", "next", "Next"),
        Binding("p", "prev", "Previous"),
        Binding("up", "volume_up", "Volume+"),
        Binding("down", "volume_down", "Volume-"),
        Binding("m", "mute", "Mute"),
        Binding("s", "shuffle", "Shuffle"),
        Binding("r", "repeat", "Repeat"),
        Binding("t", "theme", "Theme"),
        Binding("v", "visualizer", "Visualizer"),
        Binding("l", "toggle_playlist", "Playlist"),
        Binding("?", "help", "Help"),
        Binding("right", "seek_forward", "Forward"),
        Binding("left", "seek_backward", "Back"),
    ]
    
    def __init__(self, playlist: Playlist, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.show_playlist = False
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        theme = theme_manager.current
        
        # Header with now playing
        with Container(classes="header"):
            yield Label("♪ CMP - CLI Music Player", id="app-title")
            yield Label("No track loaded", id="now-playing")
            yield Label("00:00 / 00:00", id="time-display")
        
        # Visualizer
        with Container(classes="visualizer-container"):
            self.visualizer = VisualizerWidget(classes="visualizer")
            self.visualizer.set_colors(
                theme.colors.visualizer_primary,
                theme.colors.background
            )
            yield self.visualizer
        
        # Progress bar
        with Container(classes="progress-container"):
            self.progress_bar = ProgressBar(classes="progress-bar")
            self.progress_bar.set_chars(
                theme.chars.progress_filled,
                theme.chars.progress_empty
            )
            yield self.progress_bar
        
        # Controls
        with Horizontal(classes="controls-container"):
            with Horizontal(classes="playback-controls"):
                yield Label(theme.chars.shuffle, id="shuffle-indicator")
                yield Label(theme.chars.repeat, id="repeat-indicator")
                yield Label(theme.chars.prev, id="btn-prev")
                yield Label(f"[ {theme.chars.play} ]", id="btn-play")
                yield Label(theme.chars.next, id="btn-next")
            
            with Horizontal(classes="volume-container"):
                self.volume_bar = VolumeBar(classes="volume-bar")
                self.volume_bar.set_chars(
                    theme.chars.volume_filled,
                    theme.chars.volume_empty,
                    "🔇"
                )
                yield self.volume_bar
        
        # Playlist (hidden by default)
        with Container(classes="playlist-container"):
            self.playlist_widget = PlaylistWidget(
                self.playlist,
                classes="playlist"
            )
            self.playlist_widget.set_colors(
                theme.colors.playlist_current,
                theme.colors.playlist_selected
            )
            self.playlist_widget.display = False
            yield self.playlist_widget
        
        # Status bar
        with Horizontal(classes="status-bar"):
            yield Label("Ready", id="status-text")
            yield Label("Vol: 70%", id="status-volume")
            yield Label("Theme: default", id="status-theme")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize on mount."""
        # Setup audio callbacks
        audio_engine.register_callback(self._on_audio_data)
        audio_engine.register_position_callback(self._on_position_change)
        
        # Initialize volume
        config = config_manager.config
        audio_engine.volume = config.player.default_volume / 100
        self.volume_bar.volume = config.player.default_volume
        
        # Setup playlist play callback
        self.playlist_widget.set_play_callback(self._play_track_at_index)
        
        # Apply theme styles
        self._apply_theme()
        
        # Update display timer
        self.set_interval(0.5, self._update_display)
    
    def _play_track_at_index(self, index: int):
        """Play track at given playlist index."""
        track = self.playlist.select(index)
        if track:
            self._load_and_play(track)
    
    def _apply_theme(self):
        """Apply current theme styles."""
        theme = theme_manager.current
        
        # Update progress bar chars
        self.progress_bar.set_chars(
            theme.chars.progress_filled,
            theme.chars.progress_empty
        )
        
        # Update volume bar chars
        self.volume_bar.set_chars(
            theme.chars.volume_filled,
            theme.chars.volume_empty,
            "🔇"
        )
        
        # Update visualizer colors
        self.visualizer.set_colors(
            theme.colors.visualizer_primary,
            theme.colors.background
        )
        
        # Update playlist colors
        self.playlist_widget.set_colors(
            theme.colors.playlist_current,
            theme.colors.playlist_selected
        )
        
        # Update control labels
        self._update_control_labels()
    
    def _update_control_labels(self):
        """Update control button labels."""
        theme = theme_manager.current
        
        # Update indicators
        self.query_one("#shuffle-indicator", Label).update(
            theme.chars.shuffle if self.playlist.shuffle else "  "
        )
        
        repeat_char = theme.chars.repeat
        if self.playlist.repeat == RepeatMode.ONE:
            repeat_char = theme.chars.repeat_one
        elif self.playlist.repeat == RepeatMode.NONE:
            repeat_char = "  "
        self.query_one("#repeat-indicator", Label).update(repeat_char)
        
        # Update play button
        play_char = theme.chars.pause if audio_engine.state == PlaybackState.PLAYING else theme.chars.play
        self.query_one("#btn-play", Label).update(f"[ {play_char} ]")
    
    def _on_audio_data(self, data):
        """Handle audio data for visualization."""
        try:
            self.visualizer.update_audio_data(data)
        except Exception:
            pass
    
    def _on_position_change(self, position: float, duration: float):
        """Handle position change."""
        self.progress_bar.progress = position
        self.progress_bar.total = duration if duration > 0 else 1
    
    def _update_display(self):
        """Update display elements."""
        # Update now playing
        track = audio_engine.current_track
        if track:
            self.query_one("#now-playing", Label).update(
                f"{track.artist} - {track.title}"
            )
            self.query_one("#time-display", Label).update(
                f"{format_duration(audio_engine.position)} / {format_duration(track.duration)}"
            )
        
        # Update play button
        self._update_control_labels()
        
        # Update volume
        self.volume_bar.volume = int(audio_engine.volume * 100)
        self.volume_bar.muted = audio_engine.muted
        
        # Update playlist current index
        self.playlist_widget.current_index = self.playlist.current_index
        
        # Update status
        self.query_one("#status-theme", Label).update(f"Theme: {theme_manager.current.name}")
    
    def action_play_pause(self):
        """Toggle play/pause."""
        if audio_engine.state == PlaybackState.PLAYING:
            audio_engine.pause()
        elif audio_engine.state == PlaybackState.PAUSED:
            audio_engine.play()
        else:
            # Try to play current track
            track = self.playlist.current_track
            if track:
                self._load_and_play(track)
    
    def action_next(self):
        """Play next track."""
        track = self.playlist.next()
        if track:
            self._load_and_play(track)
    
    def action_prev(self):
        """Play previous track."""
        track = self.playlist.previous()
        if track:
            self._load_and_play(track)
    
    def _load_and_play(self, track: Track):
        """Load and play a track."""
        if audio_engine.load(track):
            audio_engine.play()
    
    def action_volume_up(self):
        """Increase volume."""
        audio_engine.volume = min(1.0, audio_engine.volume + 0.05)
    
    def action_volume_down(self):
        """Decrease volume."""
        audio_engine.volume = max(0.0, audio_engine.volume - 0.05)
    
    def action_mute(self):
        """Toggle mute."""
        audio_engine.toggle_mute()
    
    def action_shuffle(self):
        """Toggle shuffle."""
        self.playlist.shuffle = not self.playlist.shuffle
    
    def action_repeat(self):
        """Toggle repeat mode."""
        mode = self.playlist.toggle_repeat()
        self.notify(f"Repeat: {mode.value}")
    
    def action_seek_forward(self):
        """Seek forward."""
        audio_engine.seek(audio_engine.position + 10)
    
    def action_seek_backward(self):
        """Seek backward."""
        audio_engine.seek(audio_engine.position - 10)
    
    def action_theme(self):
        """Switch theme."""
        themes = theme_manager.list_themes()
        current_idx = next((i for i, t in enumerate(themes) if t.name == theme_manager.current.name), 0)
        next_idx = (current_idx + 1) % len(themes)
        next_theme = themes[next_idx]
        
        theme_manager.apply_theme(next_theme.name)
        self._apply_theme()
        self.notify(f"Theme: {next_theme.display_name}")
    
    def action_visualizer(self):
        """Toggle visualizer type."""
        types = ["spectrum", "waveform", "compact"]
        current_idx = types.index(self.visualizer.visualizer_type) if self.visualizer.visualizer_type in types else 0
        next_type = types[(current_idx + 1) % len(types)]
        self.visualizer.set_type(next_type)
        self.notify(f"Visualizer: {next_type}")
    
    def action_toggle_playlist(self):
        """Toggle playlist visibility."""
        self.show_playlist = not self.show_playlist
        self.playlist_widget.display = self.show_playlist
    
    def action_quit(self):
        """Quit the application."""
        self.app.exit()
    
    def action_help(self):
        """Show help."""
        help_text = """
        # Keyboard Shortcuts
        
        ## Playback
        - Space: Play/Pause
        - N: Next track
        - P: Previous track
        - ←/→: Seek backward/forward 10s
        - ↑/↓: Volume up/down
        
        ## Controls
        - M: Mute
        - S: Toggle shuffle
        - R: Toggle repeat
        - T: Switch theme
        - V: Switch visualizer
        - L: Toggle playlist
        
        ## General
        - Q: Quit
        - ?: Show this help
        """
        self.notify(help_text, title="Help", timeout=10)


class MusicPlayerApp(App):
    """Main music player application."""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .header {
        height: 3;
        dock: top;
        padding: 0 1;
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
    
    .visualizer-container {
        height: 10;
        padding: 0 2;
    }
    
    .visualizer {
        height: 100%;
        content-align: center middle;
    }
    
    .progress-container {
        height: 1;
        padding: 0 2;
    }
    
    .progress-bar {
        height: 100%;
    }
    
    .controls-container {
        height: 3;
        padding: 0 2;
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
    
    .playlist-container {
        height: 1fr;
        padding: 0 2;
    }
    
    .playlist {
        height: 100%;
        border: solid $primary;
    }
    
    .status-bar {
        height: 1;
        dock: bottom;
        padding: 0 1;
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
