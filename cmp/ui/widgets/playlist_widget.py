"""Playlist widget."""
from textual.widgets import DataTable, Static
from textual.reactive import reactive
from textual.color import Color
from typing import Optional, Callable
from ...player.playlist import Playlist
from ...player.metadata import format_duration


class PlaylistWidget(Static):
    """Playlist display widget."""
    
    current_index = reactive(-1)
    
    def __init__(self, playlist: Playlist, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.playlist.register_change_callback(self._on_playlist_change)
        self._table: Optional[DataTable] = None
        self._current_color = "#00ff00"
        self._selected_color = "#1a1a1a"
        self._on_play: Optional[Callable[[int], None]] = None
    
    def set_play_callback(self, callback: Callable[[int], None]):
        """Set callback for play request."""
        self._on_play = callback
    
    def set_colors(self, current: str, selected: str):
        """Set playlist colors."""
        self._current_color = current
        self._selected_color = selected
    
    def compose(self):
        """Compose the widget."""
        from textual.widgets import DataTable
        self._table = DataTable()
        self._table.cursor_type = "row"
        self._table.zebra_stripes = True
        self._table.add_columns("#", "Title", "Artist", "Album", "Duration")
        yield self._table
    
    def on_mount(self):
        """Initialize on mount."""
        self._refresh_table()
    
    def _on_playlist_change(self):
        """Handle playlist changes."""
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh the playlist table."""
        if self._table is None:
            return
        
        self._table.clear()
        
        for i, track in enumerate(self.playlist.tracks):
            style = None
            if i == self.playlist.current_index:
                style = f"bold {self._current_color}"
            
            self._table.add_row(
                str(i + 1),
                track.title[:30],
                track.artist[:20],
                track.album[:20],
                format_duration(track.duration),
                label=str(i),
            )
    
    def watch_current_index(self, index: int):
        """Handle current index change."""
        self._refresh_table()
        if self._table and index >= 0:
            self._table.move_cursor(row=index)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Handle row selection (Enter key or click)."""
        try:
            # Use cursor_row which is the displayed row index
            index = event.cursor_row
            if 0 <= index < len(self.playlist.tracks):
                self.playlist.select(index)
                # Notify parent to play
                if self._on_play:
                    self._on_play(index)
        except Exception:
            pass
