"""MCP Server implementation for CLI Music Player."""
import asyncio
import logging
import threading
import time
from typing import Any, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
)

from ..state import PlayerState, EventBus
from ..state.events import EventType
from ..player.engine import AudioEngine, Track, PlaybackState
from ..player.playlist import Playlist, RepeatMode
from ..player.metadata import extract_metadata
from ..config.settings import ConfigManager

logger = logging.getLogger(__name__)


class MusicPlayerMCPServer:
    """MCP Server exposing music player functionality to AI agents."""
    
    def __init__(
        self,
        audio_engine: Optional[AudioEngine] = None,
        playlist: Optional[Playlist] = None,
        state: Optional[PlayerState] = None,
        config_manager: Optional[ConfigManager] = None,
    ):
        self.audio_engine = audio_engine or AudioEngine()
        self.playlist = playlist or Playlist()
        self.state = state or PlayerState()
        self.config_manager = config_manager or ConfigManager()
        
        self.server = Server("cmp-music-player")
        self._track_ended = False
        self._monitor_thread = None
        self._running = False
        
        # Setup auto-play next track when current track ends
        self._setup_auto_play_next()
        
        self._setup_handlers()
    
    def _setup_auto_play_next(self):
        """Setup auto-play next track when current track ends."""
        def on_track_end():
            # This runs in the decoder thread
            # Signal that track ended - the monitor will handle next track
            self._track_ended = True
        
        self.audio_engine.register_end_callback(on_track_end)
    
    def _start_monitor(self):
        """Start the monitor thread for auto-play next track."""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Monitor thread loop - handles auto-play next track."""
        while self._running:
            time.sleep(0.5)
            
            if self._track_ended:
                self._track_ended = False
                
                # Handle auto-play next
                if self.playlist.repeat == RepeatMode.NONE:
                    if self.playlist.current_index < len(self.playlist) - 1:
                        track = self.playlist.next()
                        if track:
                            self.audio_engine.load(track)
                            self.audio_engine.play()
                elif self.playlist.repeat == RepeatMode.ALL:
                    track = self.playlist.next()
                    if track:
                        self.audio_engine.load(track)
                        self.audio_engine.play()
                elif self.playlist.repeat == RepeatMode.ONE:
                    track = self.playlist.current_track
                    if track:
                        self.audio_engine.load(track)
                        self.audio_engine.play()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        # Register tools
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return [
                # Playback control tools
                Tool(
                    name="play",
                    description="Start or resume playback. Optionally specify a track path to play.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "track_path": {
                                "type": "string",
                                "description": "Optional path to a specific track to play"
                            }
                        }
                    }
                ),
                Tool(
                    name="pause",
                    description="Pause current playback",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="stop",
                    description="Stop playback and reset position",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="next",
                    description="Skip to next track in playlist",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="previous",
                    description="Go to previous track in playlist",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="seek",
                    description="Seek to a specific position in the current track",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "position_seconds": {
                                "type": "number",
                                "description": "Position in seconds to seek to"
                            }
                        },
                        "required": ["position_seconds"]
                    }
                ),
                Tool(
                    name="set_volume",
                    description="Set playback volume (0-100)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "volume": {
                                "type": "integer",
                                "description": "Volume level (0-100)",
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        "required": ["volume"]
                    }
                ),
                
                # Playlist management tools
                Tool(
                    name="get_playlist",
                    description="Get the current playlist with all tracks",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="add_to_playlist",
                    description="Add tracks to the playlist",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file or directory paths to add"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to add directories recursively",
                                "default": True
                            }
                        },
                        "required": ["paths"]
                    }
                ),
                Tool(
                    name="remove_from_playlist",
                    description="Remove tracks from the playlist by index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "indices": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of track indices to remove"
                            }
                        },
                        "required": ["indices"]
                    }
                ),
                Tool(
                    name="clear_playlist",
                    description="Clear all tracks from the playlist",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # Status query tools
                Tool(
                    name="get_current_track",
                    description="Get information about the currently playing track",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_player_status",
                    description="Get current player status and state",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_volume",
                    description="Get current volume level",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_position",
                    description="Get current playback position",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # Additional control tools
                Tool(
                    name="set_shuffle",
                    description="Enable or disable shuffle mode",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "Whether to enable shuffle"
                            }
                        },
                        "required": ["enabled"]
                    }
                ),
                Tool(
                    name="set_repeat",
                    description="Set repeat mode (none, all, one)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["none", "all", "one"],
                                "description": "Repeat mode"
                            }
                        },
                        "required": ["mode"]
                    }
                ),
                Tool(
                    name="jump_to_track",
                    description="Jump to a specific track in the playlist by index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the track to jump to"
                            }
                        },
                        "required": ["index"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                result = await self._handle_tool_call(name, arguments)
                return [TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="player://status",
                    name="Player Status",
                    description="Current playback status and state",
                    mimeType="application/json",
                ),
                Resource(
                    uri="player://playlist",
                    name="Current Playlist",
                    description="Current playlist with all tracks",
                    mimeType="application/json",
                ),
                Resource(
                    uri="player://config",
                    name="Configuration",
                    description="Current player configuration",
                    mimeType="application/json",
                ),
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource."""
            import json
            
            if uri == "player://status":
                return json.dumps(self._get_status_dict(), indent=2)
            elif uri == "player://playlist":
                return json.dumps(self._get_playlist_dict(), indent=2)
            elif uri == "player://config":
                return json.dumps(self.config_manager.config.model_dump(), indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _handle_tool_call(self, name: str, arguments: dict[str, Any]) -> str:
        """Handle a tool call and return result."""
        import json
        
        # Playback control
        if name == "play":
            return await self._tool_play(arguments.get("track_path"))
        elif name == "pause":
            return await self._tool_pause()
        elif name == "stop":
            return await self._tool_stop()
        elif name == "next":
            return await self._tool_next()
        elif name == "previous":
            return await self._tool_previous()
        elif name == "seek":
            return await self._tool_seek(arguments["position_seconds"])
        elif name == "set_volume":
            return await self._tool_set_volume(arguments["volume"])
        
        # Playlist management
        elif name == "get_playlist":
            return json.dumps(self._get_playlist_dict(), indent=2)
        elif name == "add_to_playlist":
            return await self._tool_add_to_playlist(
                arguments["paths"],
                arguments.get("recursive", True)
            )
        elif name == "remove_from_playlist":
            return await self._tool_remove_from_playlist(arguments["indices"])
        elif name == "clear_playlist":
            return await self._tool_clear_playlist()
        
        # Status queries
        elif name == "get_current_track":
            track = self._get_current_track_dict()
            return json.dumps(track, indent=2) if track else "No track playing"
        elif name == "get_player_status":
            return json.dumps(self._get_status_dict(), indent=2)
        elif name == "get_volume":
            return json.dumps({"volume": int(self.audio_engine.volume * 100)})
        elif name == "get_position":
            return json.dumps({
                "position": self.audio_engine.position,
                "duration": self.audio_engine.duration,
                "percentage": (
                    self.audio_engine.position / self.audio_engine.duration * 100
                    if self.audio_engine.duration > 0 else 0
                )
            })
        
        # Additional controls
        elif name == "set_shuffle":
            self.playlist.shuffle = arguments["enabled"]
            return f"Shuffle {'enabled' if arguments['enabled'] else 'disabled'}"
        elif name == "set_repeat":
            mode = RepeatMode(arguments["mode"])
            self.playlist.repeat = mode
            return f"Repeat mode set to {mode.value}"
        elif name == "jump_to_track":
            return await self._tool_jump_to_track(arguments["index"])
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    # Tool implementations
    async def _tool_play(self, track_path: Optional[str] = None) -> str:
        """Play a track."""
        if track_path:
            # Load specific track
            path = Path(track_path)
            if not path.exists():
                return f"Error: File not found: {track_path}"
            
            track = extract_metadata(path)
            if not self.audio_engine.load(track):
                return f"Error: Failed to load track: {track_path}"
            
            self.audio_engine.play()
            return f"Playing: {track.title} by {track.artist}"
        else:
            # Resume or play current track
            if self.audio_engine.state == PlaybackState.PAUSED:
                self.audio_engine.play()
                return "Playback resumed"
            elif self.playlist.current_track:
                if self.audio_engine.load(self.playlist.current_track):
                    self.audio_engine.play()
                    track = self.playlist.current_track
                    return f"Playing: {track.title} by {track.artist}"
                return "Error: Failed to load track"
            else:
                return "No track to play. Add tracks to playlist first."
    
    async def _tool_pause(self) -> str:
        """Pause playback."""
        if self.audio_engine.state == PlaybackState.PLAYING:
            self.audio_engine.pause()
            return "Playback paused"
        return "Nothing to pause"
    
    async def _tool_stop(self) -> str:
        """Stop playback."""
        self.audio_engine.stop()
        return "Playback stopped"
    
    async def _tool_next(self) -> str:
        """Next track."""
        track = self.playlist.next()
        if track:
            if self.audio_engine.load(track):
                if self.audio_engine.state == PlaybackState.PLAYING:
                    self.audio_engine.play()
                return f"Next track: {track.title} by {track.artist}"
            return "Error: Failed to load next track"
        return "No next track"
    
    async def _tool_previous(self) -> str:
        """Previous track."""
        track = self.playlist.previous()
        if track:
            if self.audio_engine.load(track):
                if self.audio_engine.state == PlaybackState.PLAYING:
                    self.audio_engine.play()
                return f"Previous track: {track.title} by {track.artist}"
            return "Error: Failed to load previous track"
        return "No previous track"
    
    async def _tool_seek(self, position_seconds: float) -> str:
        """Seek to position."""
        self.audio_engine.seek(position_seconds)
        return f"Seeked to {position_seconds:.1f}s"
    
    async def _tool_set_volume(self, volume: int) -> str:
        """Set volume."""
        self.audio_engine.volume = volume / 100.0
        return f"Volume set to {volume}%"
    
    async def _tool_add_to_playlist(self, paths: list[str], recursive: bool) -> str:
        """Add tracks to playlist."""
        total_added = 0
        for path_str in paths:
            path = Path(path_str)
            count = self.playlist.add_file(path, recursive=recursive)
            total_added += count
        
        return f"Added {total_added} track(s) to playlist. Total: {len(self.playlist)} tracks"
    
    async def _tool_remove_from_playlist(self, indices: list[int]) -> str:
        """Remove tracks from playlist."""
        removed = 0
        # Sort in reverse to avoid index shifting
        for index in sorted(indices, reverse=True):
            if self.playlist.remove(index):
                removed += 1
        
        return f"Removed {removed} track(s). Playlist now has {len(self.playlist)} tracks"
    
    async def _tool_clear_playlist(self) -> str:
        """Clear playlist."""
        self.playlist.clear()
        return "Playlist cleared"
    
    async def _tool_jump_to_track(self, index: int) -> str:
        """Jump to track."""
        track = self.playlist.select(index)
        if track:
            if self.audio_engine.load(track):
                if self.audio_engine.state == PlaybackState.PLAYING:
                    self.audio_engine.play()
                return f"Jumped to track {index}: {track.title} by {track.artist}"
            return "Error: Failed to load track"
        return f"Invalid track index: {index}"
    
    async def _tool_set_shuffle(self, enabled: bool) -> str:
        """Set shuffle mode."""
        self.playlist.shuffle = enabled
        return f"Shuffle {'enabled' if enabled else 'disabled'}"
    
    async def _tool_set_repeat(self, mode: str) -> str:
        """Set repeat mode."""
        repeat_mode = RepeatMode(mode)
        self.playlist.repeat = repeat_mode
        return f"Repeat mode set to {mode}"
    
    # Helper methods
    def _get_current_track_dict(self) -> Optional[dict]:
        """Get current track as dict."""
        track = self.audio_engine.current_track
        if not track:
            return None
        
        return {
            "path": str(track.path),
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "duration": track.duration,
        }
    
    def _get_status_dict(self) -> dict:
        """Get player status as dict."""
        return {
            "playback": {
                "status": self.audio_engine.state.name.lower(),
                "position": self.audio_engine.position,
                "duration": self.audio_engine.duration,
                "volume": int(self.audio_engine.volume * 100),
                "muted": self.audio_engine.muted,
            },
            "playlist": {
                "total_tracks": len(self.playlist),
                "current_index": self.playlist.current_index,
                "shuffle": self.playlist.shuffle,
                "repeat": self.playlist.repeat.value,
            },
            "current_track": self._get_current_track_dict(),
        }
    
    def _get_playlist_dict(self) -> dict:
        """Get playlist as dict."""
        return {
            "name": self.playlist.name,
            "total_tracks": len(self.playlist),
            "current_index": self.playlist.current_index,
            "shuffle": self.playlist.shuffle,
            "repeat": self.playlist.repeat.value,
            "tracks": [
                {
                    "index": i,
                    "path": str(track.path),
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "duration": track.duration,
                }
                for i, track in enumerate(self.playlist.tracks)
            ]
        }
    
    async def run(self):
        """Run the MCP server."""
        # Initialize audio engine
        self.audio_engine.initialize()
        
        # Start monitor thread for auto-play next
        self._start_monitor()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def create_mcp_server(
    audio_engine: Optional[AudioEngine] = None,
    playlist: Optional[Playlist] = None,
    state: Optional[PlayerState] = None,
    config_manager: Optional[ConfigManager] = None,
) -> MusicPlayerMCPServer:
    """Create an MCP server instance."""
    return MusicPlayerMCPServer(
        audio_engine=audio_engine,
        playlist=playlist,
        state=state,
        config_manager=config_manager,
    )
