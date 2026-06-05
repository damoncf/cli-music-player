"""Library manager for music library operations."""
import asyncio
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

from .database import Database
from .models import Track, Album, Artist, Tag, TrackInfo, LibraryStats

logger = logging.getLogger(__name__)


class LibraryManager:
    """Manages the music library database and operations."""
    
    DEFAULT_LIBRARY_PATH = "~/Music/library"
    SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma"}
    
    def __init__(self, library_path: str | Path | None = None):
        """Initialize library manager.
        
        Args:
            library_path: Path to library root directory.
                         Defaults to ~/Music/library
        """
        self.library_path = Path(library_path or self.DEFAULT_LIBRARY_PATH).expanduser()
        self.db_path = self.library_path / "metadata" / "library.db"
        
        # Ensure directories exist
        self.library_path.mkdir(parents=True, exist_ok=True)
        (self.library_path / "metadata").mkdir(parents=True, exist_ok=True)
        (self.library_path / "covers").mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db = Database(self.db_path)
        
        logger.info(f"Library initialized at {self.library_path}")
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file for deduplication.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from audio file using mutagen.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with metadata
        """
        from mutagen import File as MutagenFile
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        from mutagen.oggvorbis import OggVorbis
        from mutagen.mp4 import MP4
        
        metadata = {
            "title": file_path.stem,
            "artist": "",
            "album": "",
            "year": None,
            "genre": "",
            "duration": 0.0,
            "bitrate": None,
            "sample_rate": None,
        }
        
        try:
            audio = MutagenFile(str(file_path))
            
            if audio is None:
                return metadata
            
            # Get duration and audio info
            if hasattr(audio, 'info'):
                if hasattr(audio.info, 'length'):
                    metadata["duration"] = audio.info.length
                if hasattr(audio.info, 'bitrate'):
                    metadata["bitrate"] = audio.info.bitrate
                if hasattr(audio.info, 'sample_rate'):
                    metadata["sample_rate"] = audio.info.sample_rate
            
            # Extract tags based on file type
            if isinstance(audio, MP3):
                metadata["title"] = str(audio.get('TIT2', [metadata["title"]])[0])
                metadata["artist"] = str(audio.get('TPE1', [""])[0])
                metadata["album"] = str(audio.get('TALB', [""])[0])
                if 'TDRC' in audio:
                    try:
                        metadata["year"] = int(str(audio['TDRC'][0])[:4])
                    except (ValueError, IndexError):
                        pass
                metadata["genre"] = str(audio.get('TCON', [""])[0])
            
            elif isinstance(audio, FLAC):
                metadata["title"] = str(audio.get('title', [metadata["title"]])[0])
                metadata["artist"] = str(audio.get('artist', [""])[0])
                metadata["album"] = str(audio.get('album', [""])[0])
                if 'date' in audio:
                    try:
                        metadata["year"] = int(str(audio['date'][0])[:4])
                    except (ValueError, IndexError):
                        pass
                metadata["genre"] = str(audio.get('genre', [""])[0])
            
            elif isinstance(audio, OggVorbis):
                metadata["title"] = str(audio.get('title', [metadata["title"]])[0])
                metadata["artist"] = str(audio.get('artist', [""])[0])
                metadata["album"] = str(audio.get('album', [""])[0])
                if 'date' in audio:
                    try:
                        metadata["year"] = int(str(audio['date'][0])[:4])
                    except (ValueError, IndexError):
                        pass
                metadata["genre"] = str(audio.get('genre', [""])[0])
            
            elif isinstance(audio, MP4):
                metadata["title"] = str(audio.get('\xa9nam', [metadata["title"]])[0])
                metadata["artist"] = str(audio.get('\xa9ART', [""])[0])
                metadata["album"] = str(audio.get('\xa9alb', [""])[0])
                if '\xa9day' in audio:
                    try:
                        metadata["year"] = int(str(audio['\xa9day'][0])[:4])
                    except (ValueError, IndexError):
                        pass
                metadata["genre"] = str(audio.get('\xa9gen', [""])[0])
            
            else:
                # Generic fallback
                if 'title' in audio:
                    metadata["title"] = str(audio['title'][0])
                if 'artist' in audio:
                    metadata["artist"] = str(audio['artist'][0])
                if 'album' in audio:
                    metadata["album"] = str(audio['album'][0])
        
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    def add_track(
        self,
        file_path: str | Path,
        source: str = "local",
        source_id: Optional[str] = None,
        source_url: Optional[str] = None,
        compute_hash: bool = True,
    ) -> Optional[int]:
        """Add a track to the library.
        
        Args:
            file_path: Path to the audio file
            source: Source type ('local', 'jamendo', 'fma', etc.)
            source_id: ID from the source platform
            source_url: Original URL from source
            compute_hash: Whether to compute file hash for deduplication
            
        Returns:
            Track ID if successful, None otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {file_path.suffix}")
            return None
        
        # Compute hash for deduplication
        file_hash = None
        if compute_hash:
            file_hash = self._compute_file_hash(file_path)
            # Check if file already exists
            existing = self.db.fetchone(
                "SELECT id FROM tracks WHERE file_hash = ?", (file_hash,)
            )
            if existing:
                logger.info(f"Track already exists in library: {file_path}")
                return existing["id"]
        
        # Check if path already exists
        existing = self.db.fetchone(
            "SELECT id FROM tracks WHERE path = ?", (str(file_path),)
        )
        if existing:
            logger.info(f"Path already in library: {file_path}")
            return existing["id"]
        
        # Extract metadata
        metadata = self._extract_metadata(file_path)
        
        # Insert into database
        track_id = self.db.insert(
            """
            INSERT INTO tracks 
            (path, title, artist, album, year, genre, duration, bitrate, sample_rate,
             source, source_id, source_url, file_hash, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(file_path),
                metadata["title"],
                metadata["artist"],
                metadata["album"],
                metadata["year"],
                metadata["genre"],
                metadata["duration"],
                metadata["bitrate"],
                metadata["sample_rate"],
                source,
                source_id,
                source_url,
                file_hash,
                datetime.now(),
            ),
        )
        
        # Update artist and album stats
        self._update_artist_stats(metadata["artist"])
        self._update_album_stats(metadata["album"], metadata["artist"])
        
        logger.info(f"Added track: {metadata['title']} by {metadata['artist']}")
        return track_id
    
    def _update_artist_stats(self, artist: str) -> None:
        """Update artist statistics."""
        if not artist:
            return
        
        self.db.update(
            """
            INSERT INTO artists (name, track_count) VALUES (?, 1)
            ON CONFLICT(name) DO UPDATE SET track_count = track_count + 1
            """,
            (artist,),
        )
    
    def _update_album_stats(self, album: str, artist: str) -> None:
        """Update album statistics."""
        if not album:
            return
        
        self.db.update(
            """
            INSERT INTO albums (name, artist, track_count) VALUES (?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET track_count = track_count + 1
            WHERE name = ? AND artist = ?
            """,
            (album, artist, album, artist),
        )
    
    def search(self, query: str, limit: int = 50) -> list[Track]:
        """Full-text search for tracks.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching tracks
        """
        # Use FTS5 for full-text search
        results = self.db.fetchall(
            """
            SELECT t.* FROM tracks t
            JOIN tracks_fts fts ON t.id = fts.rowid
            WHERE tracks_fts MATCH ?
            ORDER BY t.play_count DESC
            LIMIT ?
            """,
            (query, limit),
        )
        
        return [Track.from_row(dict(row)) for row in results]
    
    def get_by_artist(self, artist: str, limit: int = 100) -> list[Track]:
        """Get tracks by artist.
        
        Args:
            artist: Artist name
            limit: Maximum number of results
            
        Returns:
            List of tracks by the artist
        """
        results = self.db.fetchall(
            """
            SELECT * FROM tracks 
            WHERE artist LIKE ? 
            ORDER BY album, title
            LIMIT ?
            """,
            (f"%{artist}%", limit),
        )
        
        return [Track.from_row(dict(row)) for row in results]
    
    def get_by_album(self, album: str, artist: Optional[str] = None) -> list[Track]:
        """Get tracks by album.
        
        Args:
            album: Album name
            artist: Optional artist name for disambiguation
            
        Returns:
            List of tracks in the album
        """
        if artist:
            results = self.db.fetchall(
                """
                SELECT * FROM tracks 
                WHERE album LIKE ? AND artist LIKE ?
                ORDER BY title
                """,
                (f"%{album}%", f"%{artist}%"),
            )
        else:
            results = self.db.fetchall(
                """
                SELECT * FROM tracks 
                WHERE album LIKE ?
                ORDER BY artist, title
                """,
                (f"%{album}%",),
            )
        
        return [Track.from_row(dict(row)) for row in results]
    
    def get_random(self, count: int = 10, genre: Optional[str] = None) -> list[Track]:
        """Get random tracks.
        
        Args:
            count: Number of tracks to return
            genre: Optional genre filter
            
        Returns:
            List of random tracks
        """
        if genre:
            results = self.db.fetchall(
                """
                SELECT * FROM tracks 
                WHERE genre LIKE ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (f"%{genre}%", count),
            )
        else:
            results = self.db.fetchall(
                """
                SELECT * FROM tracks 
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (count,),
            )
        
        return [Track.from_row(dict(row)) for row in results]
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """Get a track by ID.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track if found, None otherwise
        """
        row = self.db.fetchone("SELECT * FROM tracks WHERE id = ?", (track_id,))
        if row:
            return Track.from_row(dict(row))
        return None
    
    def get_all_tracks(self, limit: int = 1000, offset: int = 0) -> list[Track]:
        """Get all tracks with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of tracks
        """
        results = self.db.fetchall(
            """
            SELECT * FROM tracks 
            ORDER BY date_added DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        
        return [Track.from_row(dict(row)) for row in results]
    
    def update_play_stats(self, track_id: int) -> None:
        """Update play statistics for a track.
        
        Args:
            track_id: Track ID
        """
        self.db.update(
            """
            UPDATE tracks 
            SET play_count = play_count + 1,
                last_played = ?
            WHERE id = ?
            """,
            (datetime.now(), track_id),
        )
    
    def scan_directory(
        self,
        path: str | Path,
        recursive: bool = True,
        progress_callback: Optional[callable] = None,
    ) -> int:
        """Scan a directory for audio files and add to library.
        
        Args:
            path: Directory path to scan
            recursive: Whether to scan recursively
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of tracks added
        """
        path = Path(path).expanduser().resolve()
        
        if not path.exists():
            logger.error(f"Directory not found: {path}")
            return 0
        
        if not path.is_dir():
            logger.error(f"Not a directory: {path}")
            return 0
        
        count = 0
        
        if recursive:
            file_iterator = path.rglob("*")
        else:
            file_iterator = path.glob("*")
        
        for file_path in file_iterator:
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            try:
                track_id = self.add_track(file_path, compute_hash=True)
                if track_id:
                    count += 1
                
                if progress_callback:
                    progress_callback(file_path, count)
                    
            except Exception as e:
                logger.error(f"Error adding {file_path}: {e}")
        
        logger.info(f"Scanned {path}: added {count} tracks")
        return count
    
    async def scan_directory_async(
        self,
        path: str | Path,
        recursive: bool = True,
        progress_callback: Optional[callable] = None,
    ) -> int:
        """Async version of scan_directory.
        
        Args:
            path: Directory path to scan
            recursive: Whether to scan recursively
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of tracks added
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.scan_directory(path, recursive, progress_callback),
        )
    
    def cleanup_missing(self) -> int:
        """Remove entries for files that no longer exist.
        
        Returns:
            Number of entries removed
        """
        results = self.db.fetchall("SELECT id, path FROM tracks")
        removed = 0
        
        for row in results:
            path = Path(row["path"])
            if not path.exists():
                self.db.delete("DELETE FROM tracks WHERE id = ?", (row["id"],))
                removed += 1
                logger.info(f"Removed missing file: {path}")
        
        logger.info(f"Cleanup complete: removed {removed} missing entries")
        return removed
    
    def get_stats(self) -> LibraryStats:
        """Get library statistics.
        
        Returns:
            LibraryStats object with statistics
        """
        # Total counts
        total_tracks = self.db.fetchone("SELECT COUNT(*) as count FROM tracks")["count"]
        total_albums = self.db.fetchone("SELECT COUNT(*) as count FROM albums")["count"]
        total_artists = self.db.fetchone("SELECT COUNT(*) as count FROM artists")["count"]
        
        # Total duration
        duration_result = self.db.fetchone("SELECT SUM(duration) as total FROM tracks")
        total_duration = duration_result["total"] or 0.0
        
        # Tracks by genre
        genre_results = self.db.fetchall(
            """
            SELECT genre, COUNT(*) as count 
            FROM tracks 
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre
            ORDER BY count DESC
            """
        )
        tracks_by_genre = {row["genre"]: row["count"] for row in genre_results}
        
        # Tracks by source
        source_results = self.db.fetchall(
            """
            SELECT source, COUNT(*) as count 
            FROM tracks 
            GROUP BY source
            """
        )
        tracks_by_source = {row["source"]: row["count"] for row in source_results}
        
        # Tracks by year
        year_results = self.db.fetchall(
            """
            SELECT year, COUNT(*) as count 
            FROM tracks 
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
            """
        )
        tracks_by_year = {row["year"]: row["count"] for row in year_results}
        
        # Recently added (last 7 days)
        recently_added = self.db.fetchone(
            """
            SELECT COUNT(*) as count 
            FROM tracks 
            WHERE date_added >= datetime('now', '-7 days')
            """
        )["count"]
        
        # Most played tracks
        most_played_results = self.db.fetchall(
            """
            SELECT * FROM tracks 
            ORDER BY play_count DESC
            LIMIT 10
            """
        )
        most_played = [Track.from_row(dict(row)) for row in most_played_results]
        
        # Calculate total file size
        total_size = 0
        for row in self.db.fetchall("SELECT path FROM tracks"):
            try:
                total_size += Path(row["path"]).stat().st_size
            except (FileNotFoundError, OSError):
                pass
        
        return LibraryStats(
            total_tracks=total_tracks,
            total_albums=total_albums,
            total_artists=total_artists,
            total_duration=total_duration,
            total_size=total_size,
            tracks_by_genre=tracks_by_genre,
            tracks_by_source=tracks_by_source,
            tracks_by_year=tracks_by_year,
            recently_added=recently_added,
            most_played=most_played,
        )
    
    def delete_track(self, track_id: int) -> bool:
        """Delete a track from the library.
        
        Args:
            track_id: Track ID
            
        Returns:
            True if deleted, False if not found
        """
        result = self.db.delete("DELETE FROM tracks WHERE id = ?", (track_id,))
        return result > 0
    
    def get_albums(self, limit: int = 100) -> list[Album]:
        """Get all albums.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of albums
        """
        results = self.db.fetchall(
            """
            SELECT * FROM albums 
            ORDER BY name
            LIMIT ?
            """,
            (limit,),
        )
        return [Album.from_row(dict(row)) for row in results]
    
    def get_artists(self, limit: int = 100) -> list[Artist]:
        """Get all artists.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of artists
        """
        results = self.db.fetchall(
            """
            SELECT * FROM artists 
            ORDER BY name
            LIMIT ?
            """,
            (limit,),
        )
        return [Artist.from_row(dict(row)) for row in results]
    
    def add_tags(self, track_id: int, tags: list[str]) -> None:
        """Add tags to a track.
        
        Args:
            track_id: Track ID
            tags: List of tag names
        """
        for tag_name in tags:
            # Insert tag if not exists
            self.db.update(
                """
                INSERT OR IGNORE INTO tags (name) VALUES (?)
                """,
                (tag_name,),
            )
            
            # Get tag ID
            tag_row = self.db.fetchone("SELECT id FROM tags WHERE name = ?", (tag_name,))
            if tag_row:
                # Link track to tag
                self.db.update(
                    """
                    INSERT OR IGNORE INTO track_tags (track_id, tag_id) VALUES (?, ?)
                    """,
                    (track_id, tag_row["id"]),
                )
    
    def get_tracks_by_tag(self, tag: str, limit: int = 100) -> list[Track]:
        """Get tracks by tag.
        
        Args:
            tag: Tag name
            limit: Maximum number of results
            
        Returns:
            List of tracks with the tag
        """
        results = self.db.fetchall(
            """
            SELECT t.* FROM tracks t
            JOIN track_tags tt ON t.id = tt.track_id
            JOIN tags tg ON tt.tag_id = tg.id
            WHERE tg.name = ?
            LIMIT ?
            """,
            (tag, limit),
        )
        return [Track.from_row(dict(row)) for row in results]