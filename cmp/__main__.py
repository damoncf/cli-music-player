"""CLI Music Player - Main entry point."""
import sys
import asyncio
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


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--theme", "-t", default=None, help="Theme name")
@click.option("--no-visualizer", is_flag=True, help="Disable visualizer")
@click.option("--volume", "-v", default=None, type=int, help="Initial volume (0-100)")
@click.option("--shuffle", "-s", is_flag=True, help="Enable shuffle")
@click.option("--loop", "-l", default="none", type=click.Choice(["none", "all", "one"]), help="Loop mode")
@click.version_option(version="0.1.0", prog_name="cmp")
def main(
    ctx: click.Context,
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
        cmp daemon --port 8080
        cmp mcp
    """
    # If no subcommand, run the default player
    if ctx.invoked_subcommand is None:
        ctx.invoke(play, paths=paths, theme=theme, no_visualizer=no_visualizer,
                   volume=volume, shuffle=shuffle, loop=loop)


@main.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--theme", "-t", default=None, help="Theme name")
@click.option("--no-visualizer", is_flag=True, help="Disable visualizer")
@click.option("--volume", "-v", default=None, type=int, help="Initial volume (0-100)")
@click.option("--shuffle", "-s", is_flag=True, help="Enable shuffle")
@click.option("--loop", "-l", default="none", type=click.Choice(["none", "all", "one"]), help="Loop mode")
def play(
    paths: tuple[str],
    theme: str | None,
    no_visualizer: bool,
    volume: int | None,
    shuffle: bool,
    loop: str,
):
    """Start the interactive music player (default)."""
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


@main.command()
@click.option("--port", "-p", default=8080, type=int, help="Port to listen on")
@click.option("--host", "-h", default="localhost", help="Host to bind to")
def daemon(port: int, host: str):
    """Run as a background daemon with HTTP/WebSocket API."""
    from .daemon import run_daemon
    
    click.echo(f"Starting daemon on http://{host}:{port}")
    click.echo("Press Ctrl+C to stop")
    
    try:
        asyncio.run(run_daemon(port=port, host=host))
    except KeyboardInterrupt:
        click.echo("\nDaemon stopped")


@main.command()
def mcp():
    """Run as an MCP server for AI agent integration."""
    from .mcp_server import create_mcp_server
    
    click.echo("Starting MCP server...", err=True)
    
    server = create_mcp_server()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        click.echo("\nMCP server stopped", err=True)


@main.command()
@click.argument("command", type=click.Choice(["play", "pause", "stop", "next", "prev", "status", "volume"]))
@click.option("--path", "-p", default=None, help="Track path (for play command)")
@click.option("--value", "-v", default=None, type=int, help="Value (for volume command)")
@click.option("--port", default=8080, type=int, help="Daemon port")
def client(command: str, path: str | None, value: int | None, port: int):
    """Control a running daemon instance."""
    import aiohttp
    import json
    
    async def send_request():
        base_url = f"http://localhost:{port}"
        
        async with aiohttp.ClientSession() as session:
            if command == "play":
                if path:
                    async with session.post(f"{base_url}/api/play", 
                                          json={"path": path}) as resp:
                        data = await resp.json()
                else:
                    async with session.post(f"{base_url}/api/play") as resp:
                        data = await resp.json()
            elif command == "pause":
                async with session.post(f"{base_url}/api/pause") as resp:
                    data = await resp.json()
            elif command == "stop":
                async with session.post(f"{base_url}/api/stop") as resp:
                    data = await resp.json()
            elif command == "next":
                async with session.post(f"{base_url}/api/next") as resp:
                    data = await resp.json()
            elif command == "prev":
                async with session.post(f"{base_url}/api/previous") as resp:
                    data = await resp.json()
            elif command == "status":
                async with session.get(f"{base_url}/api/status") as resp:
                    data = await resp.json()
            elif command == "volume":
                if value is None:
                    click.echo("Error: --value required for volume command", err=True)
                    return
                async with session.post(f"{base_url}/api/volume", 
                                      json={"volume": value}) as resp:
                    data = await resp.json()
            
            click.echo(json.dumps(data, indent=2))
    
    try:
        asyncio.run(send_request())
    except Exception as e:
        click.echo(f"Error connecting to daemon: {e}", err=True)
        click.echo(f"Make sure daemon is running on port {port}", err=True)


if __name__ == "__main__":
    main()
