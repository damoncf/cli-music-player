"""Playlist management."""
import json
import random
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import fnmatch

from .engine import Track


class RepeatMode(Enum):
    """Repeat modes."""
    NONE = "none"
    ALL = "all"
    ONE = "one"


class SortBy(Enum):
    """Sort options."""
    NAME = "name"
    ARTIST = "artist"
    ALBUM = "album"
    DURATION = "duration"
    CUSTOM = "custom"


class Playlist:
    """Manages a playlist of tracks."""
    
    def __init__(self, name: str = "Playlist"):
        self.name = name
        self._tracks: List[Track] = []
        self._current_index: int = -1
        self._shuffle: bool = False
        self._repeat: RepeatMode = RepeatMode.NONE
        self._shuffled_indices: List[int] = []
        self._history: List[int] = []
        self._history_index: int = -1
        
        self._change_callbacks: List[Callable] = []
    
    def register_change_callback(self, callback: Callable):
        """Register callback for playlist changes."""
        self._change_callbacks.append(callback)
    
    def _notify_change(self):
        """Notify all registered callbacks."""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception:
                pass
    
    @property
    def tracks(self) -> List[Track]:
        """Get all tracks."""
        return self._tracks.copy()
    
    @property
    def current_index(self) -> int:
        """Get current track index."""
        return self._current_index
    
    @property
    def current_track(self) -> Optional[Track]:
        """Get current track."""
        if 0 <= self._current_index < len(self._tracks):
            return self._tracks[self._current_index]
        return None
    
    @property
    def shuffle(self) -> bool:
        """Get shuffle state."""
        return self._shuffle
    
    @shuffle.setter
    def shuffle(self, value: bool):
        """Set shuffle state."""
        self._shuffle = value
        if value:
            self._regenerate_shuffle()
    
    @property
    def repeat(self) -> RepeatMode:
        """Get repeat mode."""
        return self._repeat
    
    @repeat.setter
    def repeat(self, value: RepeatMode):
        """Set repeat mode."""
        self._repeat = value
    
    def toggle_repeat(self) -> RepeatMode:
        """Toggle repeat mode. Returns new mode."""
        modes = [RepeatMode.NONE, RepeatMode.ALL, RepeatMode.ONE]
        idx = modes.index(self._repeat)
        self._repeat = modes[(idx + 1) % len(modes)]
        return self._repeat
    
    def _regenerate_shuffle(self):
        """Regenerate shuffled indices."""
        self._shuffled_indices = list(range(len(self._tracks)))
        if len(self._shuffled_indices) > 1:
            random.shuffle(self._shuffled_indices)
    
    def add(self, track: Track):
        """Add a track to playlist."""
        self._tracks.append(track)
        if self._shuffle:
            self._regenerate_shuffle()
        self._notify_change()
    
    def add_file(self, path: Path, recursive: bool = False) -> int:
        """Add file(s) to playlist. Returns number of tracks added."""
        from .metadata import extract_metadata
        
        count = 0
        path = Path(path)
        
        if path.is_file():
            try:
                track = extract_metadata(path)
                self.add(track)
                count += 1
            except Exception:
                pass
        elif path.is_dir() and recursive:
            for ext in ["*.mp3", "*.flac", "*.wav", "*.aac", "*.ogg", "*.m4a"]:
                for file_path in path.rglob(ext):
                    try:
                        track = extract_metadata(file_path)
                        self.add(track)
                        count += 1
                    except Exception:
                        pass
        
        return count
    
    def remove(self, index: int) -> bool:
        """Remove track at index. Returns success."""
        if 0 <= index < len(self._tracks):
            self._tracks.pop(index)
            if index < self._current_index:
                self._current_index -= 1
            elif index == self._current_index:
                self._current_index = -1
            if self._shuffle:
                self._regenerate_shuffle()
            self._notify_change()
            return True
        return False
    
    def clear(self):
        """Clear all tracks."""
        self._tracks.clear()
        self._current_index = -1
        self._shuffled_indices.clear()
        self._notify_change()
    
    def select(self, index: int) -> Optional[Track]:
        """Select track by index."""
        if 0 <= index < len(self._tracks):
            self._current_index = index
            return self._tracks[index]
        return None
    
    def next(self) -> Optional[Track]:
        """Get next track."""
        if not self._tracks:
            return None
        
        if self._repeat == RepeatMode.ONE:
            return self.current_track
        
        if self._shuffle:
            if self._current_index < 0:
                self._current_index = self._shuffled_indices[0] if self._shuffled_indices else 0
            else:
                current_shuffled_pos = self._shuffled_indices.index(self._current_index)
                next_shuffled_pos = (current_shuffled_pos + 1) % len(self._shuffled_indices)
                self._current_index = self._shuffled_indices[next_shuffled_pos]
        else:
            self._current_index = (self._current_index + 1) % len(self._tracks)
        
        return self.current_track
    
    def previous(self) -> Optional[Track]:
        """Get previous track."""
        if not self._tracks:
            return None
        
        if self._repeat == RepeatMode.ONE:
            return self.current_track
        
        if self._shuffle:
            if self._current_index < 0:
                self._current_index = self._shuffled_indices[-1] if self._shuffled_indices else 0
            else:
                current_shuffled_pos = self._shuffled_indices.index(self._current_index)
                prev_shuffled_pos = (current_shuffled_pos - 1) % len(self._shuffled_indices)
                self._current_index = self._shuffled_indices[prev_shuffled_pos]
        else:
            self._current_index = (self._current_index - 1) % len(self._tracks)
        
        return self.current_track
    
    def sort(self, by: SortBy, reverse: bool = False):
        """Sort playlist."""
        if by == SortBy.NAME:
            self._tracks.sort(key=lambda t: t.title.lower(), reverse=reverse)
        elif by == SortBy.ARTIST:
            self._tracks.sort(key=lambda t: (t.artist.lower(), t.title.lower()), reverse=reverse)
        elif by == SortBy.ALBUM:
            self._tracks.sort(key=lambda t: (t.album.lower(), t.title.lower()), reverse=reverse)
        elif by == SortBy.DURATION:
            self._tracks.sort(key=lambda t: t.duration, reverse=reverse)
        
        self._current_index = -1
        if self._shuffle:
            self._regenerate_shuffle()
        self._notify_change()
    
    def search(self, query: str) -> List[tuple[int, Track]]:
        """Search tracks. Returns list of (index, track) tuples."""
        query = query.lower()
        results = []
        for i, track in enumerate(self._tracks):
            if (query in track.title.lower() or 
                query in track.artist.lower() or 
                query in track.album.lower()):
                results.append((i, track))
        return results
    
    def save(self, path: Path):
        """Save playlist to file."""
        path = Path(path)
        if path.suffix == ".m3u":
            self._save_m3u(path)
        else:
            self._save_json(path)
    
    def _save_json(self, path: Path):
        """Save as JSON."""
        data = {
            "version": "1.0",
            "name": self.name,
            "tracks": [
                {
                    "path": str(t.path),
                    "title": t.title,
                    "artist": t.artist,
                    "album": t.album,
                    "duration": t.duration,
                }
                for t in self._tracks
            ]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_m3u(self, path: Path):
        """Save as M3U."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for track in self._tracks:
                f.write(f"#EXTINF:{int(track.duration)},{track.artist} - {track.title}\n")
                f.write(f"{track.path}\n")
    
    @classmethod
    def load(cls, path: Path) -> "Playlist":
        """Load playlist from file."""
        path = Path(path)
        if path.suffix == ".m3u":
            return cls._load_m3u(path)
        else:
            return cls._load_json(path)
    
    @classmethod
    def _load_json(cls, path: Path) -> "Playlist":
        """Load from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        playlist = cls(name=data.get("name", "Playlist"))
        from .metadata import extract_metadata
        
        for t_data in data.get("tracks", []):
            try:
                track = Track(
                    path=Path(t_data["path"]),
                    title=t_data.get("title", ""),
                    artist=t_data.get("artist", ""),
                    album=t_data.get("album", ""),
                    duration=t_data.get("duration", 0.0),
                )
                playlist.add(track)
            except Exception:
                pass
        
        return playlist
    
    @classmethod
    def _load_m3u(cls, path: Path) -> "Playlist":
        """Load from M3U."""
        playlist = cls(name=path.stem)
        from .metadata import extract_metadata
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF:"):
                # Parse EXTINF
                parts = line[8:].split(",", 1)
                duration = int(parts[0]) if parts[0].isdigit() else 0
                title_artist = parts[1] if len(parts) > 1 else ""
                
                # Next line is path
                i += 1
                if i < len(lines):
                    file_path = Path(lines[i].strip())
                    if not file_path.is_absolute():
                        file_path = path.parent / file_path
                    
                    try:
                        track = extract_metadata(file_path)
                        if title_artist and " - " in title_artist:
                            artist, title = title_artist.split(" - ", 1)
                            track.artist = artist
                            track.title = title
                        playlist.add(track)
                    except Exception:
                        pass
            i += 1
        
        return playlist
    
    def __len__(self) -> int:
        """Get track count."""
        return len(self._tracks)
    
    def __getitem__(self, index: int) -> Track:
        """Get track by index."""
        return self._tracks[index]
