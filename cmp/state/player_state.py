"""Centralized player state management."""
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import logging
from enum import Enum

from pydantic import BaseModel

from .events import EventBus, Event, EventType

logger = logging.getLogger(__name__)


class PlaybackStatus(str, Enum):
    """Playback status."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class RepeatMode(str, Enum):
    """Repeat modes."""
    NONE = "none"
    ALL = "all"
    ONE = "one"


# Pydantic models for type-safe state
class TrackInfo(BaseModel):
    """Track information."""
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    
    class Config:
        use_enum_values = True


class PlaybackState(BaseModel):
    """Playback state."""
    status: PlaybackStatus = PlaybackStatus.IDLE
    current_track: Optional[TrackInfo] = None
    position: float = 0.0
    volume: int = 70
    muted: bool = False
    shuffle: bool = False
    repeat: RepeatMode = RepeatMode.NONE
    
    class Config:
        use_enum_values = True


class PlaylistState(BaseModel):
    """Playlist state."""
    tracks: list[TrackInfo] = []
    current_index: int = -1
    name: str = "Playlist"
    
    class Config:
        use_enum_values = True


class ConfigState(BaseModel):
    """Configuration state."""
    theme: str = "default"
    visualizer_type: str = "spectrum"
    visualizer_enabled: bool = True
    
    class Config:
        use_enum_values = True


@dataclass
class StateSnapshot:
    """Immutable state snapshot for undo/redo."""
    playback: PlaybackState
    playlist: PlaylistState
    config: ConfigState
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "playback": self.playback.model_dump(),
            "playlist": self.playlist.model_dump(),
            "config": self.config.model_dump(),
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StateSnapshot":
        """Create from dictionary."""
        return cls(
            playback=PlaybackState(**data["playback"]),
            playlist=PlaylistState(**data["playlist"]),
            config=ConfigState(**data["config"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class StateChange:
    """Represents a state change."""
    path: str  # e.g., "playback.volume"
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)


class PlayerState:
    """Centralized state management with reactive updates."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._playback = PlaybackState()
        self._playlist = PlaylistState()
        self._config = ConfigState()
        
        self._event_bus = event_bus or EventBus()
        self._subscribers: list[Callable[[StateChange], None]] = []
        self._snapshots: list[StateSnapshot] = []
        self._snapshot_index = -1
        self._max_snapshots = 50
        
        self._persistence_path: Optional[Path] = None
        self._auto_save = True
    
    # Properties for state access
    @property
    def playback(self) -> PlaybackState:
        """Get playback state."""
        return self._playback
    
    @property
    def playlist(self) -> PlaylistState:
        """Get playlist state."""
        return self._playlist
    
    @property
    def config(self) -> ConfigState:
        """Get config state."""
        return self._config
    
    # Convenience properties
    @property
    def status(self) -> PlaybackStatus:
        """Get playback status."""
        return self._playback.status
    
    @status.setter
    def status(self, value: PlaybackStatus):
        """Set playback status."""
        self._update_state("playback.status", self._playback.status, value)
        self._playback.status = value
    
    @property
    def current_track(self) -> Optional[TrackInfo]:
        """Get current track."""
        return self._playback.current_track
    
    @current_track.setter
    def current_track(self, value: Optional[TrackInfo]):
        """Set current track."""
        self._update_state("playback.current_track", self._playback.current_track, value)
        self._playback.current_track = value
    
    @property
    def position(self) -> float:
        """Get position."""
        return self._playback.position
    
    @position.setter
    def position(self, value: float):
        """Set position."""
        self._update_state("playback.position", self._playback.position, value)
        self._playback.position = value
    
    @property
    def volume(self) -> int:
        """Get volume."""
        return self._playback.volume
    
    @volume.setter
    def volume(self, value: int):
        """Set volume."""
        value = max(0, min(100, value))
        self._update_state("playback.volume", self._playback.volume, value)
        self._playback.volume = value
    
    @property
    def muted(self) -> bool:
        """Get mute state."""
        return self._playback.muted
    
    @muted.setter
    def muted(self, value: bool):
        """Set mute state."""
        self._update_state("playback.muted", self._playback.muted, value)
        self._playback.muted = value
    
    @property
    def shuffle(self) -> bool:
        """Get shuffle state."""
        return self._playback.shuffle
    
    @shuffle.setter
    def shuffle(self, value: bool):
        """Set shuffle state."""
        self._update_state("playback.shuffle", self._playback.shuffle, value)
        self._playback.shuffle = value
    
    @property
    def repeat(self) -> RepeatMode:
        """Get repeat mode."""
        return self._playback.repeat
    
    @repeat.setter
    def repeat(self, value: RepeatMode):
        """Set repeat mode."""
        self._update_state("playback.repeat", self._playback.repeat, value)
        self._playback.repeat = value
    
    # State update methods
    def _update_state(self, path: str, old_value: Any, new_value: Any):
        """Update state and notify subscribers."""
        if old_value == new_value:
            return
        
        change = StateChange(
            path=path,
            old_value=old_value,
            new_value=new_value,
        )
        
        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(change)
            except Exception as e:
                logger.error(f"Error in state subscriber: {e}")
        
        # Emit event
        event_type = self._get_event_type(path)
        if event_type:
            self._event_bus.emit(
                event_type,
                data={"path": path, "old": old_value, "new": new_value},
                source="PlayerState"
            )
        
        # Auto-save if enabled
        if self._auto_save and self._persistence_path:
            self._schedule_save()
    
    def _get_event_type(self, path: str) -> Optional[EventType]:
        """Get event type for state path."""
        mapping = {
            "playback.status": EventType.PLAYBACK_STARTED,
            "playback.current_track": EventType.TRACK_CHANGED,
            "playback.position": EventType.POSITION_CHANGED,
            "playback.volume": EventType.VOLUME_CHANGED,
            "playback.muted": EventType.MUTE_TOGGLED,
            "playback.shuffle": EventType.SHUFFLE_TOGGLED,
            "playback.repeat": EventType.REPEAT_CHANGED,
            "playlist.tracks": EventType.PLAYLIST_CHANGED,
            "config.theme": EventType.THEME_CHANGED,
            "config.visualizer_type": EventType.VISUALIZER_CHANGED,
        }
        return mapping.get(path)
    
    # Subscription methods
    def subscribe(self, callback: Callable[[StateChange], None]):
        """Subscribe to state changes."""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[StateChange], None]):
        """Unsubscribe from state changes."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    # Snapshot methods
    def snapshot(self) -> StateSnapshot:
        """Create a state snapshot."""
        snapshot = StateSnapshot(
            playback=self._playback.model_copy(deep=True),
            playlist=self._playlist.model_copy(deep=True),
            config=self._config.model_copy(deep=True),
        )
        
        # Add to history
        self._snapshots = self._snapshots[:self._snapshot_index + 1]
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)
        self._snapshot_index = len(self._snapshots) - 1
        
        return snapshot
    
    def restore(self, snapshot: StateSnapshot):
        """Restore state from snapshot."""
        self._playback = snapshot.playback.model_copy(deep=True)
        self._playlist = snapshot.playlist.model_copy(deep=True)
        self._config = snapshot.config.model_copy(deep=True)
        
        self._event_bus.emit(
            EventType.CONFIG_CHANGED,
            data={"restored": True},
            source="PlayerState"
        )
    
    def undo(self) -> bool:
        """Undo to previous snapshot."""
        if self._snapshot_index > 0:
            self._snapshot_index -= 1
            self.restore(self._snapshots[self._snapshot_index])
            return True
        return False
    
    def redo(self) -> bool:
        """Redo to next snapshot."""
        if self._snapshot_index < len(self._snapshots) - 1:
            self._snapshot_index += 1
            self.restore(self._snapshots[self._snapshot_index])
            return True
        return False
    
    # Persistence methods
    def set_persistence_path(self, path: Path):
        """Set path for state persistence."""
        self._persistence_path = path
    
    def _schedule_save(self):
        """Schedule a save operation (debounced)."""
        # For now, save immediately
        # TODO: Implement debounced save
        self.save()
    
    def save(self):
        """Save state to file."""
        if not self._persistence_path:
            return
        
        try:
            snapshot = StateSnapshot(
                playback=self._playback,
                playlist=self._playlist,
                config=self._config,
            )
            
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persistence_path, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)
            
            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load(self) -> bool:
        """Load state from file."""
        if not self._persistence_path or not self._persistence_path.exists():
            return False
        
        try:
            with open(self._persistence_path, "r") as f:
                data = json.load(f)
            
            snapshot = StateSnapshot.from_dict(data)
            self.restore(snapshot)
            
            logger.debug("State loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False
    
    # Validation methods
    def validate(self) -> list[str]:
        """Validate current state. Returns list of errors."""
        errors = []
        
        # Validate playback state
        if self._playback.volume < 0 or self._playback.volume > 100:
            errors.append("Volume must be between 0 and 100")
        
        if self._playback.position < 0:
            errors.append("Position cannot be negative")
        
        if self._playback.current_track:
            if self._playback.position > self._playback.current_track.duration:
                errors.append("Position exceeds track duration")
        
        # Validate playlist state
        if self._playlist.current_index >= len(self._playlist.tracks):
            errors.append("Current index out of range")
        
        return errors
    
    def to_dict(self) -> dict:
        """Export state as dictionary."""
        return {
            "playback": self._playback.model_dump(),
            "playlist": self._playlist.model_dump(),
            "config": self._config.model_dump(),
        }
    
    def from_dict(self, data: dict):
        """Import state from dictionary."""
        if "playback" in data:
            self._playback = PlaybackState(**data["playback"])
        if "playlist" in data:
            self._playlist = PlaylistState(**data["playlist"])
        if "config" in data:
            self._config = ConfigState(**data["config"])


# Global state instance
player_state = PlayerState()
