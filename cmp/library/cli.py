"""CLI commands for music library management."""
import asyncio
import click
from pathlib import Path
from typing import Optional

from .manager import LibraryManager
from .models import Track


# Global library manager instance
_library_manager: Optional[LibraryManager] = None


def get_library_manager() -> LibraryManager:
    """Get or create library manager instance."""
    global _library_manager
    if _library_manager is None:
        _library_manager = LibraryManager()
    return _library_manager


@click.group()
def library():
    """Music library management commands."""
    pass


@library.command()
@click.argument("path", type=click.Path(exists=True), required=False)
@click.option("--recursive", "-r", is_flag=True, default=True, help="Scan recursively")
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def scan(path: Optional[str], recursive: bool, library_path: Optional[str]):
    """Scan directory for music files and add to library.
    
    If PATH is not specified, scans the default library directory.
    """
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    scan_path = Path(path) if path else manager.library_path / "local"
    
    click.echo(f"Scanning {scan_path}...")
    
    def progress_callback(file_path: Path, count: int):
        click.echo(f"\r  Processed: {count} files", nl=False)
    
    count = manager.scan_directory(scan_path, recursive=recursive, progress_callback=progress_callback)
    click.echo(f"\n\nAdded {count} tracks to library.")


@library.command()
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def stats(library_path: Optional[str]):
    """Show library statistics."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    stats = manager.get_stats()
    
    click.echo("\n📊 Library Statistics\n")
    click.echo(f"  Total tracks:    {stats.total_tracks:,}")
    click.echo(f"  Total albums:    {stats.total_albums:,}")
    click.echo(f"  Total artists:   {stats.total_artists:,}")
    
    # Format duration
    hours = int(stats.total_duration // 3600)
    minutes = int((stats.total_duration % 3600) // 60)
    click.echo(f"  Total duration:  {hours}h {minutes}m")
    
    # Format size
    size_gb = stats.total_size / (1024 ** 3)
    size_mb = stats.total_size / (1024 ** 2)
    if size_gb >= 1:
        click.echo(f"  Total size:      {size_gb:.2f} GB")
    else:
        click.echo(f"  Total size:      {size_mb:.2f} MB")
    
    click.echo(f"  Recently added:  {stats.recently_added} (last 7 days)")
    
    # Top genres
    if stats.tracks_by_genre:
        click.echo("\n🎵 Top Genres")
        for genre, count in list(stats.tracks_by_genre.items())[:5]:
            click.echo(f"  {genre or 'Unknown'}: {count}")
    
    # Top sources
    if stats.tracks_by_source:
        click.echo("\n📁 Tracks by Source")
        for source, count in stats.tracks_by_source.items():
            click.echo(f"  {source}: {count}")
    
    # Most played
    if stats.most_played:
        click.echo("\n🔥 Most Played")
        for track in stats.most_played[:5]:
            if track.play_count > 0:
                click.echo(f"  {track.artist} - {track.title} ({track.play_count} plays)")


@library.command()
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Maximum number of results")
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def search(query: str, limit: int, library_path: Optional[str]):
    """Search for tracks in the library.
    
    Uses full-text search on title, artist, album, and genre.
    """
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    results = manager.search(query, limit=limit)
    
    if not results:
        click.echo(f"No results found for '{query}'")
        return
    
    click.echo(f"\n🔍 Search Results for '{query}' ({len(results)} found)\n")
    
    for i, track in enumerate(results, 1):
        duration = format_duration(track.duration)
        click.echo(f"  {i:3}. {track.artist or 'Unknown Artist'} - {track.title}")
        click.echo(f"       Album: {track.album or 'Unknown'} | Duration: {duration}")
        if track.genre:
            click.echo(f"       Genre: {track.genre}")
        click.echo()


@library.command()
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def cleanup(library_path: Optional[str]):
    """Remove entries for files that no longer exist."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    click.echo("Cleaning up missing files...")
    removed = manager.cleanup_missing()
    click.echo(f"Removed {removed} missing entries from library.")


@library.command("list")
@click.option("--limit", "-n", default=50, help="Maximum number of tracks to show")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--artist", "-a", help="Filter by artist")
@click.option("--album", "-b", help="Filter by album")
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def list_tracks(limit: int, offset: int, artist: Optional[str], album: Optional[str], library_path: Optional[str]):
    """List tracks in the library."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    if artist:
        tracks = manager.get_by_artist(artist, limit=limit)
        click.echo(f"\n🎵 Tracks by '{artist}'\n")
    elif album:
        tracks = manager.get_by_album(album)
        click.echo(f"\n💿 Tracks in album '{album}'\n")
    else:
        tracks = manager.get_all_tracks(limit=limit, offset=offset)
        click.echo(f"\n🎵 Library Tracks ({len(tracks)} shown)\n")
    
    if not tracks:
        click.echo("  No tracks found.")
        return
    
    for i, track in enumerate(tracks, offset + 1):
        duration = format_duration(track.duration)
        click.echo(f"  {i:4}. {track.artist or 'Unknown':30} - {track.title[:40]:40} [{duration}]")


@library.command()
@click.argument("count", type=int, default=10)
@click.option("--genre", "-g", help="Filter by genre")
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def random(count: int, genre: Optional[str], library_path: Optional[str]):
    """Get random tracks from the library."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    tracks = manager.get_random(count=count, genre=genre)
    
    if not tracks:
        click.echo("No tracks found.")
        return
    
    click.echo(f"\n🎲 {len(tracks)} Random Tracks")
    if genre:
        click.echo(f"   Genre: {genre}")
    click.echo()
    
    for i, track in enumerate(tracks, 1):
        duration = format_duration(track.duration)
        click.echo(f"  {i:3}. {track.artist or 'Unknown'} - {track.title} [{duration}]")


@library.command()
@click.argument("track_id", type=int)
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def info(track_id: int, library_path: Optional[str]):
    """Show detailed information about a track."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    track = manager.get_track(track_id)
    
    if not track:
        click.echo(f"Track {track_id} not found.")
        return
    
    click.echo(f"\n🎵 Track Information\n")
    click.echo(f"  ID:          {track.id}")
    click.echo(f"  Title:       {track.title}")
    click.echo(f"  Artist:      {track.artist or 'Unknown'}")
    click.echo(f"  Album:       {track.album or 'Unknown'}")
    click.echo(f"  Year:        {track.year or 'Unknown'}")
    click.echo(f"  Genre:       {track.genre or 'Unknown'}")
    click.echo(f"  Duration:    {format_duration(track.duration)}")
    if track.bitrate:
        click.echo(f"  Bitrate:     {track.bitrate} kbps")
    else:
        click.echo("  Bitrate:     Unknown")
    if track.sample_rate:
        click.echo(f"  Sample Rate: {track.sample_rate} Hz")
    else:
        click.echo("  Sample Rate: Unknown")
    click.echo(f"\n  Path:        {track.path}")
    click.echo(f"  Source:      {track.source}")
    if track.source_url:
        click.echo(f"  Source URL:  {track.source_url}")
    click.echo(f"\n  Play Count:  {track.play_count}")
    if track.last_played:
        click.echo(f"  Last Played: {track.last_played}")
    if track.date_added:
        click.echo(f"  Date Added:  {track.date_added}")


@library.command()
@click.argument("track_id", type=int)
@click.option("--library-path", "-l", type=click.Path(), help="Custom library path")
def delete(track_id: int, library_path: Optional[str]):
    """Delete a track from the library."""
    manager = LibraryManager(library_path) if library_path else get_library_manager()
    
    track = manager.get_track(track_id)
    if not track:
        click.echo(f"Track {track_id} not found.")
        return
    
    if click.confirm(f"Delete '{track.title}' by '{track.artist}'?"):
        if manager.delete_track(track_id):
            click.echo("Track deleted.")
        else:
            click.echo("Failed to delete track.")


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    if seconds <= 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"