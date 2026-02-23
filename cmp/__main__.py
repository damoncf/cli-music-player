"""CLI Music Player - Main entry point."""
import sys
import click
from pathlib import Path

from .player.engine import audio_engine, Track
from .player.playlist import Playlist
from .player.metadata import extract_metadata
from .config.settings import config_manager
from .themes.manager import theme_manager
from .ui.app import MusicPlayerApp


def load_files_to_playlist(playlist: Playlist, paths: list[str]):
    """Load files and folders into playlist."""
    for path_str in paths:
        path = Path(path_str).expanduser().resolve()
        
        if path.is_file():
            try:
                track = extract_metadata(path)
                playlist.add(track)
            except Exception as e:
                click.echo(f"Error loading {path}: {e}", err=True)
        
        elif path.is_dir():
            for ext in ["*.mp3", "*.flac", "*.wav", "*.aac", "*.ogg", "*.m4a"]:
                for file_path in path.rglob(ext):
                    try:
                        track = extract_metadata(file_path)
                        playlist.add(track)
                    except Exception as e:
                        click.echo(f"Error loading {file_path}: {e}", err=True)


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--theme", "-t", default=None, help="Theme name")
@click.option("--no-visualizer", is_flag=True, help="Disable visualizer")
@click.option("--volume", "-v", default=None, type=int, help="Initial volume (0-100)")
@click.option("--shuffle", "-s", is_flag=True, help="Enable shuffle")
@click.option("--loop", "-l", default="none", type=click.Choice(["none", "all", "one"]), help="Loop mode")
@click.version_option(version="0.1.0", prog_name="cmp")
def main(
    paths: tuple[str],
    theme: str | None,
    no_visualizer: bool,
    volume: int | None,
    shuffle: bool,
    loop: str,
):
    """
    CMP - CLI Music Player
    
    A terminal-based music player with audio visualization.
    
    Examples:
        cmp song.mp3
        cmp ~/Music/
        cmp -t neon playlist.m3u
    """
    # Load configuration
    config = config_manager.config
    
    # Apply command line overrides
    if theme:
        if not theme_manager.apply_theme(theme):
            click.echo(f"Warning: Theme '{theme}' not found", err=True)
    
    if no_visualizer:
        config.visualizer.enabled = False
    
    if volume is not None:
        config.player.default_volume = max(0, min(100, volume))
    
    # Create playlist
    playlist = Playlist(name="Current")
    
    # Load files
    if paths:
        load_files_to_playlist(playlist, list(paths))
    
    # Apply playback settings
    if shuffle:
        playlist.shuffle = True
    
    from .player.playlist import RepeatMode
    playlist.repeat = RepeatMode(loop)
    
    # Select first track
    if playlist.tracks:
        playlist.select(0)
        if config.player.auto_play:
            track = playlist.current_track
            if track:
                audio_engine.load(track)
                audio_engine.play()
    
    # Start UI
    try:
        app = MusicPlayerApp(playlist)
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        audio_engine.shutdown()
        config_manager.save()


if __name__ == "__main__":
    main()
