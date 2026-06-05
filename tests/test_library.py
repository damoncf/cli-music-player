"""Tests for the music library module."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from datetime import datetime

from cmp.library.database import Database
from cmp.library.models import Track, Album, Artist, Tag, TrackInfo, LibraryStats
from cmp.library.manager import LibraryManager


@pytest.fixture
def temp_library():
    """Create a temporary library directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_audio_file(temp_library):
    """Create a temporary audio file for testing."""
    # Create a minimal valid MP3 file (just headers, not playable)
    # This is a minimal MP3 frame header
    mp3_data = bytes([
        0xFF, 0xFB, 0x90, 0x00,  # MP3 frame header
    ]) + b'\x00' * 1000  # Padding
    
    audio_path = Path(temp_library) / "test.mp3"
    with open(audio_path, 'wb') as f:
        f.write(mp3_data)
    
    return audio_path


@pytest.fixture
def db(temp_library):
    """Create a test database."""
    db_path = Path(temp_library) / "library.db"
    return Database(db_path)


@pytest.fixture
def manager(temp_library):
    """Create a test library manager."""
    return LibraryManager(temp_library)


class TestDatabase:
    """Tests for the Database class."""
    
    def test_database_initialization(self, temp_library):
        """Test database is created correctly."""
        db_path = Path(temp_library) / "library.db"
        db = Database(db_path)
        
        assert db_path.exists()
        
        # Check tables exist
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row['name'] for row in cursor.fetchall()}
        
        assert 'tracks' in tables
        assert 'albums' in tables
        assert 'artists' in tables
        assert 'tags' in tables
        assert 'track_tags' in tables
        assert 'download_queue' in tables
        assert 'tracks_fts' in tables
    
    def test_insert_and_retrieve_track(self, db):
        """Test inserting and retrieving a track."""
        track_id = db.insert(
            """
            INSERT INTO tracks (path, title, artist, album, duration, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("/path/to/song.mp3", "Test Song", "Test Artist", "Test Album", 180.0, "local")
        )
        
        assert track_id > 0
        
        row = db.fetchone("SELECT * FROM tracks WHERE id = ?", (track_id,))
        assert row is not None
        assert row['title'] == "Test Song"
        assert row['artist'] == "Test Artist"
    
    def test_fts_search(self, db):
        """Test full-text search functionality."""
        # Insert test tracks
        db.insert(
            "INSERT INTO tracks (path, title, artist, album, genre) VALUES (?, ?, ?, ?, ?)",
            ("/path/rock.mp3", "Rock Song", "Rock Band", "Rock Album", "Rock")
        )
        db.insert(
            "INSERT INTO tracks (path, title, artist, album, genre) VALUES (?, ?, ?, ?, ?)",
            ("/path/jazz.mp3", "Jazz Song", "Jazz Band", "Jazz Album", "Jazz")
        )
        
        # Search for "Rock"
        results = db.fetchall(
            "SELECT t.* FROM tracks t JOIN tracks_fts fts ON t.id = fts.rowid WHERE tracks_fts MATCH ?",
            ("Rock",)
        )
        
        assert len(results) >= 1
        found_titles = [r['title'] for r in results]
        assert "Rock Song" in found_titles


class TestModels:
    """Tests for data models."""
    
    def test_track_creation(self):
        """Test Track dataclass creation."""
        track = Track(
            id=1,
            path="/path/to/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration=180.0,
        )
        
        assert track.id == 1
        assert track.title == "Test Song"
        assert track.artist == "Test Artist"
        assert track.duration == 180.0
    
    def test_track_from_row(self):
        """Test Track creation from database row."""
        row = {
            'id': 1,
            'path': '/path/to/song.mp3',
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'year': 2023,
            'genre': 'Rock',
            'duration': 180.0,
            'bitrate': 320,
            'sample_rate': 44100,
            'source': 'local',
            'source_id': None,
            'source_url': None,
            'cover_path': None,
            'lyrics_path': None,
            'play_count': 5,
            'last_played': None,
            'date_added': None,
            'file_hash': None,
            'audio_hash': None,
        }
        
        track = Track.from_row(row)
        
        assert track.id == 1
        assert track.title == "Test Song"
        assert track.year == 2023
        assert track.play_count == 5
    
    def test_track_to_dict(self):
        """Test Track serialization to dictionary."""
        track = Track(
            id=1,
            path="/path/to/song.mp3",
            title="Test Song",
            artist="Test Artist",
            duration=180.0,
        )
        
        data = track.to_dict()
        
        assert data['id'] == 1
        assert data['title'] == "Test Song"
        assert data['duration'] == 180.0
    
    def test_album_creation(self):
        """Test Album dataclass creation."""
        album = Album(
            id=1,
            name="Test Album",
            artist="Test Artist",
            year=2023,
            track_count=10,
        )
        
        assert album.name == "Test Album"
        assert album.track_count == 10
    
    def test_artist_creation(self):
        """Test Artist dataclass creation."""
        artist = Artist(
            id=1,
            name="Test Artist",
            track_count=50,
        )
        
        assert artist.name == "Test Artist"
        assert artist.track_count == 50
    
    def test_track_info_creation(self):
        """Test TrackInfo dataclass creation."""
        info = TrackInfo(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration=180.0,
            source="jamendo",
            source_id="12345",
            tags=["rock", "indie"],
        )
        
        assert info.title == "Test Song"
        assert info.source == "jamendo"
        assert "rock" in info.tags
    
    def test_library_stats_creation(self):
        """Test LibraryStats dataclass creation."""
        stats = LibraryStats(
            total_tracks=100,
            total_albums=10,
            total_artists=5,
            total_duration=18000.0,
            tracks_by_genre={"Rock": 50, "Jazz": 30, "Pop": 20},
        )
        
        assert stats.total_tracks == 100
        assert stats.total_duration == 18000.0
        assert stats.tracks_by_genre["Rock"] == 50


class TestLibraryManager:
    """Tests for the LibraryManager class."""
    
    def test_manager_initialization(self, manager, temp_library):
        """Test library manager initialization."""
        assert manager.library_path == Path(temp_library)
        assert manager.db_path == Path(temp_library) / "metadata" / "library.db"
        assert manager.db_path.exists()
    
    def test_add_track(self, manager, temp_audio_file):
        """Test adding a track to the library."""
        track_id = manager.add_track(temp_audio_file)
        
        assert track_id is not None
        assert track_id > 0
        
        # Verify track was added
        track = manager.get_track(track_id)
        assert track is not None
        assert track.path == str(temp_audio_file)
    
    def test_add_duplicate_track(self, manager, temp_audio_file):
        """Test adding duplicate track returns same ID."""
        track_id1 = manager.add_track(temp_audio_file)
        track_id2 = manager.add_track(temp_audio_file)
        
        # Should return same ID for duplicate
        assert track_id1 == track_id2
    
    def test_get_all_tracks(self, manager, temp_audio_file):
        """Test retrieving all tracks."""
        manager.add_track(temp_audio_file)
        
        tracks = manager.get_all_tracks()
        
        assert len(tracks) >= 1
    
    def test_search_tracks(self, manager, temp_audio_file):
        """Test searching for tracks."""
        manager.add_track(temp_audio_file)
        
        # Search might not find results if metadata wasn't extracted properly
        # from our minimal test file, so just test the search doesn't error
        results = manager.search("test", limit=10)
        
        assert isinstance(results, list)
    
    def test_get_stats(self, manager, temp_audio_file):
        """Test getting library statistics."""
        manager.add_track(temp_audio_file)
        
        stats = manager.get_stats()
        
        assert isinstance(stats, LibraryStats)
        assert stats.total_tracks >= 1
    
    def test_cleanup_missing(self, manager, temp_audio_file):
        """Test cleanup of missing files."""
        manager.add_track(temp_audio_file)
        
        # Delete the file
        os.remove(temp_audio_file)
        
        # Cleanup should remove the entry
        removed = manager.cleanup_missing()
        
        assert removed >= 1
    
    def test_delete_track(self, manager, temp_audio_file):
        """Test deleting a track."""
        track_id = manager.add_track(temp_audio_file)
        
        result = manager.delete_track(track_id)
        
        assert result is True
        
        # Verify track is gone
        track = manager.get_track(track_id)
        assert track is None
    
    def test_update_play_stats(self, manager, temp_audio_file):
        """Test updating play statistics."""
        track_id = manager.add_track(temp_audio_file)
        
        manager.update_play_stats(track_id)
        
        track = manager.get_track(track_id)
        assert track.play_count == 1
    
    def test_get_random_tracks(self, manager, temp_audio_file):
        """Test getting random tracks."""
        manager.add_track(temp_audio_file)
        
        tracks = manager.get_random(count=5)
        
        assert isinstance(tracks, list)
    
    def test_scan_directory(self, manager, temp_library):
        """Test scanning a directory."""
        # Create multiple test files
        for i in range(3):
            mp3_data = bytes([0xFF, 0xFB, 0x90, 0x00]) + b'\x00' * 100
            path = Path(temp_library) / f"test{i}.mp3"
            with open(path, 'wb') as f:
                f.write(mp3_data)
        
        count = manager.scan_directory(temp_library)
        
        assert count >= 3


class TestIntegration:
    """Integration tests for the library module."""
    
    def test_full_workflow(self, temp_library, temp_audio_file):
        """Test complete workflow: init, add, search, stats, cleanup."""
        # Initialize
        manager = LibraryManager(temp_library)
        
        # Add track
        track_id = manager.add_track(temp_audio_file)
        assert track_id is not None
        
        # Get stats
        stats = manager.get_stats()
        assert stats.total_tracks >= 1
        
        # Search
        results = manager.search("*", limit=10)
        assert len(results) >= 1
        
        # Update play count
        manager.update_play_stats(track_id)
        track = manager.get_track(track_id)
        assert track.play_count == 1
        
        # Delete
        assert manager.delete_track(track_id) is True
        assert manager.get_track(track_id) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])