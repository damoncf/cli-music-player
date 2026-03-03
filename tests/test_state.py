"""Tests for state management."""
import pytest
from datetime import datetime

from cmp.state import PlayerState, StateSnapshot, EventBus, EventType
from cmp.state.player_state import PlaybackState, PlaylistState, ConfigState, TrackInfo, PlaybackStatus


@pytest.fixture
def player_state():
    """Create a PlayerState instance for testing."""
    return PlayerState()


@pytest.fixture
def event_bus():
    """Create an EventBus instance for testing."""
    return EventBus()


class TestPlayerState:
    """Tests for PlayerState."""
    
    def test_initial_state(self, player_state):
        """Test initial state values."""
        assert player_state.status == PlaybackStatus.IDLE
        assert player_state.current_track is None
        assert player_state.position == 0.0
        assert player_state.volume == 70
        assert not player_state.muted
        assert not player_state.shuffle
    
    def test_set_volume(self, player_state):
        """Test volume setting."""
        player_state.volume = 50
        assert player_state.volume == 50
        
        # Test bounds
        player_state.volume = 150
        assert player_state.volume == 100
        
        player_state.volume = -10
        assert player_state.volume == 0
    
    def test_set_status(self, player_state):
        """Test status setting."""
        player_state.status = PlaybackStatus.PLAYING
        assert player_state.status == PlaybackStatus.PLAYING
        
        player_state.status = PlaybackStatus.PAUSED
        assert player_state.status == PlaybackStatus.PAUSED
    
    def test_set_current_track(self, player_state):
        """Test setting current track."""
        track = TrackInfo(
            path="/test/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration=180.0
        )
        
        player_state.current_track = track
        assert player_state.current_track == track
        assert player_state.current_track.title == "Test Song"
    
    def test_snapshot(self, player_state):
        """Test state snapshot creation."""
        player_state.volume = 80
        player_state.shuffle = True
        
        snapshot = player_state.snapshot()
        
        assert snapshot.playback.volume == 80
        assert snapshot.playback.shuffle is True
        assert isinstance(snapshot.timestamp, datetime)
    
    def test_restore(self, player_state):
        """Test state restoration from snapshot."""
        player_state.volume = 80
        player_state.shuffle = True
        snapshot = player_state.snapshot()
        
        # Modify state
        player_state.volume = 50
        player_state.shuffle = False
        
        # Restore
        player_state.restore(snapshot)
        
        assert player_state.volume == 80
        assert player_state.shuffle is True
    
    def test_undo_redo(self, player_state):
        """Test undo/redo functionality."""
        player_state.volume = 50
        player_state.snapshot()
        
        player_state.volume = 80
        player_state.snapshot()
        
        player_state.volume = 100
        player_state.snapshot()
        
        # Undo
        assert player_state.undo() is True
        assert player_state.volume == 80
        
        assert player_state.undo() is True
        assert player_state.volume == 50
        
        # Can't undo further
        assert player_state.undo() is False
        
        # Redo
        assert player_state.redo() is True
        assert player_state.volume == 80
        
        assert player_state.redo() is True
        assert player_state.volume == 100
    
    def test_subscribe(self, player_state):
        """Test state change subscription."""
        changes = []
        
        def callback(change):
            changes.append(change)
        
        player_state.subscribe(callback)
        player_state.volume = 50
        
        assert len(changes) == 1
        assert changes[0].path == "playback.volume"
        assert changes[0].old_value == 70
        assert changes[0].new_value == 50
    
    def test_validate(self, player_state):
        """Test state validation."""
        # Valid state
        errors = player_state.validate()
        assert len(errors) == 0
        
        # Invalid volume
        player_state._playback.volume = 150
        errors = player_state.validate()
        assert len(errors) > 0
        assert "Volume" in errors[0]
    
    def test_to_dict(self, player_state):
        """Test state export to dict."""
        player_state.volume = 80
        data = player_state.to_dict()
        
        assert "playback" in data
        assert "playlist" in data
        assert "config" in data
        assert data["playback"]["volume"] == 80
    
    def test_from_dict(self, player_state):
        """Test state import from dict."""
        data = {
            "playback": {
                "status": "playing",
                "volume": 90,
                "shuffle": True,
            },
            "playlist": {
                "name": "Test Playlist",
            },
            "config": {
                "theme": "neon",
            }
        }
        
        player_state.from_dict(data)
        
        assert player_state.status == PlaybackStatus.PLAYING
        assert player_state.volume == 90
        assert player_state.shuffle is True
        assert player_state.playlist.name == "Test Playlist"
        assert player_state.config.theme == "neon"


class TestEventBus:
    """Tests for EventBus."""
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus):
        """Test event subscription and publishing."""
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.VOLUME_CHANGED, callback)
        
        await event_bus.start()
        
        event_bus.emit(EventType.VOLUME_CHANGED, {"volume": 80})
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        assert len(received_events) == 1
        assert received_events[0].data["volume"] == 80
        
        await event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_async_subscribe(self, event_bus):
        """Test async event subscription."""
        received_events = []
        
        async def async_callback(event):
            received_events.append(event)
        
        event_bus.subscribe_async(EventType.TRACK_CHANGED, async_callback)
        
        await event_bus.start()
        
        event_bus.emit(EventType.TRACK_CHANGED, {"title": "Test Song"})
        
        await asyncio.sleep(0.2)
        
        assert len(received_events) == 1
        assert received_events[0].data["title"] == "Test Song"
        
        await event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_event_history(self, event_bus):
        """Test event history."""
        await event_bus.start()
        
        event_bus.emit(EventType.VOLUME_CHANGED, {"volume": 80})
        event_bus.emit(EventType.VOLUME_CHANGED, {"volume": 90})
        
        await asyncio.sleep(0.2)
        
        history = event_bus.get_history(EventType.VOLUME_CHANGED)
        assert len(history) == 2
        
        await event_bus.stop()


class TestStateSnapshot:
    """Tests for StateSnapshot."""
    
    def test_to_dict(self):
        """Test snapshot serialization."""
        playback = PlaybackState(volume=80, shuffle=True)
        playlist = PlaylistState(name="Test Playlist")
        config = ConfigState(theme="neon")
        
        snapshot = StateSnapshot(
            playback=playback,
            playlist=playlist,
            config=config,
        )
        
        data = snapshot.to_dict()
        
        assert data["playback"]["volume"] == 80
        assert data["playback"]["shuffle"] is True
        assert data["playlist"]["name"] == "Test Playlist"
        assert data["config"]["theme"] == "neon"
        assert "timestamp" in data
    
    def test_from_dict(self):
        """Test snapshot deserialization."""
        data = {
            "playback": {
                "status": "playing",
                "volume": 90,
                "shuffle": False,
            },
            "playlist": {
                "name": "Restored Playlist",
            },
            "config": {
                "theme": "default",
            },
            "timestamp": "2026-03-03T12:00:00",
        }
        
        snapshot = StateSnapshot.from_dict(data)
        
        assert snapshot.playback.volume == 90
        assert snapshot.playlist.name == "Restored Playlist"
        assert snapshot.config.theme == "default"


# Import asyncio for async tests
import asyncio
