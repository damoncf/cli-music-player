"""SQLite database management for music library."""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class Database:
    """SQLite database manager for music library."""
    
    def __init__(self, db_path: str | Path):
        """Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            # Tracks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    year INTEGER,
                    genre TEXT,
                    duration REAL,
                    bitrate INTEGER,
                    sample_rate INTEGER,
                    
                    -- Source information
                    source TEXT,
                    source_id TEXT,
                    source_url TEXT,
                    
                    -- Metadata
                    cover_path TEXT,
                    lyrics_path TEXT,
                    
                    -- Statistics
                    play_count INTEGER DEFAULT 0,
                    last_played TIMESTAMP,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Hash for deduplication
                    file_hash TEXT UNIQUE,
                    audio_hash TEXT
                )
            """)
            
            # Albums table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    artist TEXT,
                    year INTEGER,
                    cover_path TEXT,
                    track_count INTEGER DEFAULT 0,
                    total_duration REAL DEFAULT 0.0
                )
            """)
            
            # Artists table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    bio TEXT,
                    image_path TEXT,
                    track_count INTEGER DEFAULT 0
                )
            """)
            
            # Tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            """)
            
            # Track-Tags junction table (many-to-many)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS track_tags (
                    track_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (track_id, tag_id),
                    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """)
            
            # Download queue table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    source_id TEXT,
                    url TEXT,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_date_added ON tracks(date_added)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_albums_name ON albums(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_albums_artist ON albums(artist)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name)")
            
            # Create FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS tracks_fts USING fts5(
                    title, artist, album, genre,
                    content='tracks',
                    content_rowid='id'
                )
            """)
            
            # Triggers to keep FTS in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS tracks_ai AFTER INSERT ON tracks BEGIN
                    INSERT INTO tracks_fts(rowid, title, artist, album, genre)
                    VALUES (new.id, new.title, new.artist, new.album, new.genre);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS tracks_ad AFTER DELETE ON tracks BEGIN
                    INSERT INTO tracks_fts(tracks_fts, rowid, title, artist, album, genre)
                    VALUES('delete', old.id, old.title, old.artist, old.album, old.genre);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS tracks_au AFTER UPDATE ON tracks BEGIN
                    INSERT INTO tracks_fts(tracks_fts, rowid, title, artist, album, genre)
                    VALUES('delete', old.id, old.title, old.artist, old.album, old.genre);
                    INSERT INTO tracks_fts(rowid, title, artist, album, genre)
                    VALUES (new.id, new.title, new.artist, new.album, new.genre);
                END
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        with self.get_connection() as conn:
            return conn.execute(query, params)
    
    def executemany(self, query: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """Execute a query with multiple parameter sets."""
        with self.get_connection() as conn:
            return conn.executemany(query, params_list)
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
    
    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute query and fetch all results."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def insert(self, query: str, params: tuple = ()) -> int:
        """Execute insert query and return last row id."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def update(self, query: str, params: tuple = ()) -> int:
        """Execute update query and return affected row count."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def delete(self, query: str, params: tuple = ()) -> int:
        """Execute delete query and return affected row count."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
