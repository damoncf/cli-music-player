"""Main player screen with layout and visualizer support."""
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding

from ...player.engine import audio_engine, PlaybackState
from ...player.playlist import Playlist, RepeatMode
from ...player.metadata import format_duration
from ...config.settings import config_manager
from ...themes.manager import theme_manager
from ...visualizer.manager import visualizer_manager
from ..layouts.base import layout_manager


class PlayerScreen(Screen):
    """Main player screen with dynamic layout support."""
    
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
        Binding("V", "visualizer_prev", "Visualizer (Prev)"),
        Binding("ctrl+v", "visualizer_menu", "Visualizer Menu"),
        Binding("l", "toggle_playlist", "Playlist"),
        Binding("L", "layout", "Layout"),
        Binding("ctrl+l", "layout_menu", "Layout Menu"),
        Binding("?", "help", "Help"),
        Binding("right", "seek_forward", "Forward"),
        Binding("left", "seek_backward", "Back"),
    ]
    
    def __init__(self, playlist: Playlist, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.show_playlist = False
        self._custom_layout_widgets = []
    
    def compose(self):
        """Compose the UI using current layout."""
        # Get current layout
        layout = layout_manager.current
        if layout is None:
            from ..layouts import DefaultLayout
            layout = DefaultLayout()
        
        # Compose widgets from layout
        self._custom_layout_widgets = layout.compose(self)
        for widget in self._custom_layout_widgets:
            yield widget
    
    def on_mount(self):
        """Initialize on mount."""
        # Setup audio callbacks
        audio_engine.register_callback(self._on_audio_data)
        audio_engine.register_position_callback(self._on_position_change)
        audio_engine.register_end_callback(self._on_track_end)
        
        # Initialize volume
        config = config_manager.config
        audio_engine.volume = config.player.default_volume / 100
        if hasattr(self, 'volume_bar') and self.volume_bar:
            self.volume_bar.volume = config.player.default_volume
        
        # Setup playlist play callback
        if hasattr(self, 'playlist_widget') and self.playlist_widget:
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
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.set_chars(
                theme.chars.progress_filled,
                theme.chars.progress_empty
            )
        
        # Update volume bar chars
        if hasattr(self, 'volume_bar') and self.volume_bar:
            self.volume_bar.set_chars(
                theme.chars.volume_filled,
                theme.chars.volume_empty,
                "🔇"
            )
        
        # Update visualizer colors
        if hasattr(self, 'visualizer') and self.visualizer:
            self.visualizer.set_colors(
                theme.colors.visualizer_primary,
                theme.colors.background
            )
        
        # Update playlist colors
        if hasattr(self, 'playlist_widget') and self.playlist_widget:
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
        try:
            self.query_one("#shuffle-indicator").update(
                theme.chars.shuffle if self.playlist.shuffle else "  "
            )
        except Exception:
            pass
        
        try:
            repeat_char = theme.chars.repeat
            if self.playlist.repeat == RepeatMode.ONE:
                repeat_char = theme.chars.repeat_one
            elif self.playlist.repeat == RepeatMode.NONE:
                repeat_char = "  "
            self.query_one("#repeat-indicator").update(repeat_char)
        except Exception:
            pass
        
        # Update play button
        try:
            play_char = theme.chars.pause if audio_engine.state == PlaybackState.PLAYING else theme.chars.play
            self.query_one("#btn-play").update(f"[ {play_char} ]")
        except Exception:
            pass
    
    def _on_audio_data(self, data):
        """Handle audio data for visualization."""
        if hasattr(self, 'visualizer') and self.visualizer:
            try:
                self.visualizer.update_audio_data(data)
            except Exception:
                pass
    
    def _on_position_change(self, position: float, duration: float):
        """Handle position change."""
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.progress = position
            self.progress_bar.total = duration if duration > 0 else 1
    
    def _on_track_end(self):
        """Handle track end - auto play next track."""
        # Use call_from_thread to safely update UI from audio thread
        self.app.call_from_thread(self._play_next_track)
    
    def _play_next_track(self):
        """Play next track (called from main thread)."""
        track = self.playlist.next()
        if track:
            self._load_and_play(track)
    
    def _update_display(self):
        """Update display elements."""
        # Update now playing
        track = audio_engine.current_track
        if track:
            try:
                self.query_one("#now-playing").update(
                    f"{track.artist} - {track.title}"
                )
                self.query_one("#time-display").update(
                    f"{format_duration(audio_engine.position)} / {format_duration(track.duration)}"
                )
            except Exception:
                pass
        
        # Update play button
        self._update_control_labels()
        
        # Update volume
        if hasattr(self, 'volume_bar') and self.volume_bar:
            self.volume_bar.volume = int(audio_engine.volume * 100)
            self.volume_bar.muted = audio_engine.muted
        
        # Update playlist current index
        if hasattr(self, 'playlist_widget') and self.playlist_widget:
            self.playlist_widget.current_index = self.playlist.current_index
        
        # Update status
        try:
            self.query_one("#status-theme").update(f"Theme: {theme_manager.current.name}")
            self.query_one("#status-volume").update(f"Vol: {int(audio_engine.volume * 100)}%")
        except Exception:
            pass
    
    def _reload_layout(self, layout_name: str = None):
        """Reload the screen with a new layout."""
        if layout_name:
            layout_manager.switch_to(layout_name)
        
        # Remove all current widgets (except system widgets)
        for child in list(self.children):
            if not child.id or not child.id.startswith('textual-'):
                child.remove()
        
        # Re-compose
        layout = layout_manager.current
        self._custom_layout_widgets = layout.compose(self)
        for widget in self._custom_layout_widgets:
            self.mount(widget)
        
        # Re-initialize
        self.on_mount()
    
    # Actions
    def action_play_pause(self):
        """Toggle play/pause."""
        if audio_engine.state == PlaybackState.PLAYING:
            audio_engine.pause()
        elif audio_engine.state == PlaybackState.PAUSED:
            audio_engine.play()
        else:
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
    
    def _load_and_play(self, track):
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
        """Switch to next visualizer."""
        new_viz = visualizer_manager.next()
        self.notify(f"Visualizer: {new_viz}")
    
    def action_visualizer_prev(self):
        """Switch to previous visualizer."""
        new_viz = visualizer_manager.next(reverse=True)
        self.notify(f"Visualizer: {new_viz}")
    
    def action_visualizer_menu(self):
        """Open visualizer selection menu."""
        def on_select(result):
            if result:
                self.notify(f"Visualizer: {result}")
        
        from .menus import VisualizerMenu
        self.push_screen(VisualizerMenu(), callback=on_select)
    
    def action_toggle_playlist(self):
        """Toggle playlist visibility."""
        self.show_playlist = not self.show_playlist
        if hasattr(self, 'playlist_widget') and self.playlist_widget:
            self.playlist_widget.display = self.show_playlist
    
    def action_layout(self):
        """Switch to next layout."""
        new_layout = layout_manager.next()
        self.notify(f"Layout: {new_layout}")
        self._reload_layout()
    
    def action_layout_menu(self):
        """Open layout selection menu."""
        def on_select(result):
            if result:
                self.notify(f"Layout: {result}")
                self._reload_layout(result)
        
        from .menus import LayoutMenu
        self.push_screen(LayoutMenu(), callback=on_select)
    
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
        - V: Next visualizer
        - V (shift): Previous visualizer
        - Ctrl+V: Visualizer menu
        - L: Toggle playlist
        - L (shift): Next layout
        - Ctrl+L: Layout menu
        
        ## General
        - Q: Quit
        - ?: Show this help
        """
        self.notify(help_text, title="Help", timeout=10)
