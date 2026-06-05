"""Data models for music library."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


@dataclass
class Track:
    """Represents a music track in the library."""
    id: Optional[int] = None
    path: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    year: Optional[int] = None
    genre: str = ""
    duration: float = 0.0
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    
    # Source information
    source: str = "local"  # 'local', 'jamendo', 'fma', etc.
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    
    # Metadata
    cover_path: Optional[str] = None
    lyrics_path: Optional[str] = None
    
    # Statistics
    play_count: int = 0
    last_played: Optional[datetime] = None
    date_added: Optional[datetime] = None
    
    # Hash for deduplication
    file_hash: Optional[str] = None
    audio_hash: Optional[str] = None
    
    def __post_init__(self):
        """Convert path to string if Path object."""
        if isinstance(self.path, Path):
            self.path = str(self.path)
        if isinstance(self.cover_path, Path):
            self.cover_path = str(self.cover_path)
        if isinstance(self.lyrics_path, Path):
            self.lyrics_path = str(self.lyrics_path)
    
    @classmethod
    def from_row(cls, row: dict) -> "Track":
        """Create Track from database row."""
        return cls(
            id=row.get("id"),
            path=row.get("path", ""),
            title=row.get("title", ""),
            artist=row.get("artist", ""),
            album=row.get("album", ""),
            year=row.get("year"),
            genre=row.get("genre", ""),
            duration=row.get("duration", 0.0),
            bitrate=row.get("bitrate"),
            sample_rate=row.get("sample_rate"),
            source=row.get("source", "local"),
            source_id=row.get("source_id"),
            source_url=row.get("source_url"),
            cover_path=row.get("cover_path"),
            lyrics_path=row.get("lyrics_path"),
            play_count=row.get("play_count", 0),
            last_played=row.get("last_played"),
            date_added=row.get("date_added"),
            file_hash=row.get("file_hash"),
            audio_hash=row.get("audio_hash"),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "year": self.year,
            "genre": self.genre,
            "duration": self.duration,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate,
            "source": self.source,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "cover_path": self.cover_path,
            "lyrics_path": self.lyrics_path,
            "play_count": self.play_count,
            "last_played": self.last_played.isoformat() if self.last_played else None,
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "file_hash": self.file_hash,
            "audio_hash": self.audio_hash,
        }


@dataclass
class Album:
    """Represents an album in the library."""
    id: Optional[int] = None
    name: str = ""
    artist: str = ""
    year: Optional[int] = None
    cover_path: Optional[str] = None
    track_count: int = 0
    total_duration: float = 0.0
    
    @classmethod
    def from_row(cls, row: dict) -> "Album":
        """Create Album from database row."""
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            artist=row.get("artist", ""),
            year=row.get("year"),
            cover_path=row.get("cover_path"),
            track_count=row.get("track_count", 0),
            total_duration=row.get("total_duration", 0.0),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "artist": self.artist,
            "year": self.year,
            "cover_path": self.cover_path,
            "track_count": self.track_count,
            "total_duration": self.total_duration,
        }


@dataclass
class Artist:
    """Represents an artist in the library."""
    id: Optional[int] = None
    name: str = ""
    bio: Optional[str] = None
    image_path: Optional[str] = None
    track_count: int = 0
    
    @classmethod
    def from_row(cls, row: dict) -> "Artist":
        """Create Artist from database row."""
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            bio=row.get("bio"),
            image_path=row.get("image_path"),
            track_count=row.get("track_count", 0),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "image_path": self.image_path,
            "track_count": self.track_count,
        }


@dataclass
class Tag:
    """Represents a tag in the library."""
    id: Optional[int] = None
    name: str = ""
    
    @classmethod
    def from_row(cls, row: dict) -> "Tag":
        """Create Tag from database row."""
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass
class TrackInfo:
    """Track information from crawler results.
    
    Used for tracks fetched from external sources like Jamendo, FMA, etc.
    """
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[float] = None
    source: str = ""
    source_id: Optional[str] = None
    stream_url: Optional[str] = None
    download_url: Optional[str] = None
    cover_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    license: Optional[str] = None  # CC license type
    year: Optional[int] = None
    genre: Optional[str] = None
    bitrate: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "source": self.source,
            "source_id": self.source_id,
            "stream_url": self.stream_url,
            "download_url": self.download_url,
            "cover_url": self.cover_url,
            "tags": self.tags,
            "license": self.license,
            "year": self.year,
            "genre": self.genre,
            "bitrate": self.bitrate,
        }


@dataclass
class LibraryStats:
    """Statistics about the music library."""
    total_tracks: int = 0
    total_albums: int = 0
    total_artists: int = 0
    total_duration: float = 0.0  # in seconds
    total_size: int = 0  # in bytes
    tracks_by_genre: dict[str, int] = field(default_factory=dict)
    tracks_by_source: dict[str, int] = field(default_factory=dict)
    tracks_by_year: dict[int, int] = field(default_factory=dict)
    recently_added: int = 0  # tracks added in last 7 days
    most_played: list[Track] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_tracks": self.total_tracks,
            "total_albums": self.total_albums,
            "total_artists": self.total_artists,
            "total_duration": self.total_duration,
            "total_size": self.total_size,
            "tracks_by_genre": self.tracks_by_genre,
            "tracks_by_source": self.tracks_by_source,
            "tracks_by_year": self.tracks_by_year,
            "recently_added": self.recently_added,
            "most_played": [t.to_dict() for t in self.most_played],
        }


# Pydantic models for API validation
class TrackCreate(BaseModel):
    """Schema for creating a track."""
    path: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    source: str = "local"
    source_id: Optional[str] = None
    source_url: Optional[str] = None


class TrackUpdate(BaseModel):
    """Schema for updating a track."""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None


class SearchQuery(BaseModel):
    """Schema for search query."""
    query: str
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None