"""Daemon server for headless music player operation."""
import asyncio
import json
import logging
import threading
import time
from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime
import signal
import sys

from aiohttp import web, WSMsgType

from ..player.engine import AudioEngine, Track, PlaybackState
from ..player.playlist import Playlist, RepeatMode
from ..player.metadata import extract_metadata
from ..state import PlayerState, EventBus
from ..state.events import Event, EventType
from ..config.settings import ConfigManager

logger = logging.getLogger(__name__)


class DaemonServer:
    """HTTP/WebSocket server for headless music player."""
    
    def __init__(
        self,
        audio_engine: Optional[AudioEngine] = None,
        playlist: Optional[Playlist] = None,
        state: Optional[PlayerState] = None,
        config_manager: Optional[ConfigManager] = None,
        port: int = 8080,
        host: str = "localhost",
    ):
        self.audio_engine = audio_engine or AudioEngine()
        self.playlist = playlist or Playlist()
        self.state = state or PlayerState()
        self.config_manager = config_manager or ConfigManager()
        
        self.port = port
        self.host = host
        
        self.app = web.Application()
        self._setup_routes()
        
        self._ws_clients: list[web.WebSocketResponse] = []
        self._running = False
        self._track_ended = False
        self._monitor_thread = None
        
        # Setup event forwarding to WebSocket clients
        self._setup_event_forwarding()
        
        # Setup auto-play next track when current track ends
        self._setup_auto_play_next()
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_get("/api/status", self._handle_status)
        self.app.router.add_get("/api/playlist", self._handle_playlist)
        self.app.router.add_get("/api/track", self._handle_current_track)
        self.app.router.add_post("/api/play", self._handle_play)
        self.app.router.add_post("/api/pause", self._handle_pause)
        self.app.router.add_post("/api/stop", self._handle_stop)
        self.app.router.add_post("/api/next", self._handle_next)
        self.app.router.add_post("/api/previous", self._handle_previous)
        self.app.router.add_post("/api/seek", self._handle_seek)
        self.app.router.add_post("/api/volume", self._handle_volume)
        self.app.router.add_post("/api/shuffle", self._handle_shuffle)
        self.app.router.add_post("/api/repeat", self._handle_repeat)
        self.app.router.add_post("/api/playlist/add", self._handle_playlist_add)
        self.app.router.add_post("/api/playlist/remove", self._handle_playlist_remove)
        self.app.router.add_post("/api/playlist/clear", self._handle_playlist_clear)
        self.app.router.add_post("/api/playlist/jump", self._handle_playlist_jump)
        self.app.router.add_get("/ws", self._handle_websocket)
    
    def _setup_event_forwarding(self):
        """Setup event forwarding to WebSocket clients."""
        async def forward_event(event: Event):
            if self._ws_clients:
                message = json.dumps(event.to_dict())
                for ws in self._ws_clients[:]:
                    try:
                        await ws.send_str(message)
                    except Exception:
                        self._ws_clients.remove(ws)
        
        # Subscribe to events
        event_bus = EventBus()
        for event_type in EventType:
            event_bus.subscribe_async(event_type, forward_event)
    
    def _setup_auto_play_next(self):
        """Setup auto-play next track when current track ends."""
        def on_track_end():
            # This runs in the decoder thread
            # Signal that track ended - the monitor will handle next track
            self._track_ended = True
        
        self.audio_engine.register_end_callback(on_track_end)
    
    def _start_monitor(self):
        """Start the monitor thread for auto-play next track."""
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
    
    # HTTP handlers
    async def _handle_index(self, request: web.Request) -> web.Response:
        """Handle index request."""
        return web.json_response({
            "name": "CMP Music Player Daemon",
            "version": "0.1.0",
            "endpoints": [
                "GET /api/status - Get player status",
                "GET /api/playlist - Get current playlist",
                "GET /api/track - Get current track",
                "POST /api/play - Start playback",
                "POST /api/pause - Pause playback",
                "POST /api/stop - Stop playback",
                "POST /api/next - Next track",
                "POST /api/previous - Previous track",
                "POST /api/seek - Seek to position",
                "POST /api/volume - Set volume",
                "POST /api/shuffle - Toggle shuffle",
                "POST /api/repeat - Set repeat mode",
                "POST /api/playlist/add - Add to playlist",
                "POST /api/playlist/remove - Remove from playlist",
                "POST /api/playlist/clear - Clear playlist",
                "POST /api/playlist/jump - Jump to track",
                "GET /ws - WebSocket for real-time events",
            ]
        })
    
    async def _handle_status(self, request: web.Request) -> web.Response:
        """Get player status."""
        return web.json_response(self._get_status())
    
    async def _handle_playlist(self, request: web.Request) -> web.Response:
        """Get playlist."""
        return web.json_response(self._get_playlist())
    
    async def _handle_current_track(self, request: web.Request) -> web.Response:
        """Get current track."""
        track = self.audio_engine.current_track
        if not track:
            return web.json_response({"error": "No track playing"}, status=404)
        
        return web.json_response({
            "path": str(track.path),
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "duration": track.duration,
            "position": self.audio_engine.position,
        })
    
    async def _handle_play(self, request: web.Request) -> web.Response:
        """Start playback."""
        try:
            data = await request.json()
            track_path = data.get("path")
        except:
            track_path = None
        
        if track_path:
            path = Path(track_path)
            if not path.exists():
                return web.json_response({"error": "File not found"}, status=404)
            
            track = extract_metadata(path)
            if not self.audio_engine.load(track):
                return web.json_response({"error": "Failed to load track"}, status=500)
            
            # Update playlist current_index
            for i, t in enumerate(self.playlist.tracks):
                if t.path == path:
                    self.playlist._current_index = i
                    break
        elif self.audio_engine.current_track is None and self.playlist.tracks:
            # No path given and nothing loaded — auto-load first playlist track
            track = self.playlist.tracks[0]
            self.playlist._current_index = 0
            self.audio_engine.load(track)
        
        self.audio_engine.play()
        return web.json_response({"status": "playing"})
    
    async def _handle_pause(self, request: web.Request) -> web.Response:
        """Pause playback."""
        self.audio_engine.pause()
        return web.json_response({"status": "paused"})
    
    async def _handle_stop(self, request: web.Request) -> web.Response:
        """Stop playback."""
        self.audio_engine.stop()
        return web.json_response({"status": "stopped"})
    
    async def _handle_next(self, request: web.Request) -> web.Response:
        """Next track."""
        track = self.playlist.next()
        if track:
            self.audio_engine.load(track)
            if self.audio_engine.state == PlaybackState.PLAYING:
                self.audio_engine.play()
            return web.json_response({"track": track.title})
        return web.json_response({"error": "No next track"}, status=404)
    
    async def _handle_previous(self, request: web.Request) -> web.Response:
        """Previous track."""
        track = self.playlist.previous()
        if track:
            self.audio_engine.load(track)
            if self.audio_engine.state == PlaybackState.PLAYING:
                self.audio_engine.play()
            return web.json_response({"track": track.title})
        return web.json_response({"error": "No previous track"}, status=404)
    
    async def _handle_seek(self, request: web.Request) -> web.Response:
        """Seek to position."""
        try:
            data = await request.json()
            position = float(data.get("position", 0))
        except:
            return web.json_response({"error": "Invalid position"}, status=400)
        
        self.audio_engine.seek(position)
        return web.json_response({"position": position})
    
    async def _handle_volume(self, request: web.Request) -> web.Response:
        """Set volume."""
        try:
            data = await request.json()
            volume = int(data.get("volume", 70))
        except:
            return web.json_response({"error": "Invalid volume"}, status=400)
        
        self.audio_engine.volume = volume / 100.0
        return web.json_response({"volume": volume})
    
    async def _handle_shuffle(self, request: web.Request) -> web.Response:
        """Toggle shuffle."""
        try:
            data = await request.json()
            enabled = bool(data.get("enabled", not self.playlist.shuffle))
        except:
            enabled = not self.playlist.shuffle
        
        self.playlist.shuffle = enabled
        return web.json_response({"shuffle": enabled})
    
    async def _handle_repeat(self, request: web.Request) -> web.Response:
        """Set repeat mode."""
        try:
            data = await request.json()
            mode = data.get("mode", "none")
            self.playlist.repeat = RepeatMode(mode)
        except:
            return web.json_response({"error": "Invalid mode"}, status=400)
        
        return web.json_response({"repeat": self.playlist.repeat.value})
    
    async def _handle_playlist_add(self, request: web.Request) -> web.Response:
        """Add to playlist."""
        try:
            data = await request.json()
            paths = data.get("paths", [])
            recursive = data.get("recursive", True)
        except:
            return web.json_response({"error": "Invalid request"}, status=400)
        
        total_added = 0
        for path_str in paths:
            path = Path(path_str)
            count = self.playlist.add_file(path, recursive=recursive)
            total_added += count
        
        return web.json_response({
            "added": total_added,
            "total": len(self.playlist)
        })
    
    async def _handle_playlist_remove(self, request: web.Request) -> web.Response:
        """Remove from playlist."""
        try:
            data = await request.json()
            indices = data.get("indices", [])
        except:
            return web.json_response({"error": "Invalid request"}, status=400)
        
        removed = 0
        for index in sorted(indices, reverse=True):
            if self.playlist.remove(index):
                removed += 1
        
        return web.json_response({
            "removed": removed,
            "total": len(self.playlist)
        })
    
    async def _handle_playlist_clear(self, request: web.Request) -> web.Response:
        """Clear playlist."""
        self.playlist.clear()
        return web.json_response({"total": 0})
    
    async def _handle_playlist_jump(self, request: web.Request) -> web.Response:
        """Jump to track."""
        try:
            data = await request.json()
            index = int(data.get("index", 0))
        except:
            return web.json_response({"error": "Invalid index"}, status=400)
        
        track = self.playlist.select(index)
        if track:
            self.audio_engine.load(track)
            if self.audio_engine.state == PlaybackState.PLAYING:
                self.audio_engine.play()
            return web.json_response({"track": track.title})
        
        return web.json_response({"error": "Invalid index"}, status=404)
    
    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self._ws_clients.append(ws)
        logger.info(f"WebSocket client connected. Total: {len(self._ws_clients)}")
        
        # Send initial status
        await ws.send_str(json.dumps({
            "type": "connected",
            "data": self._get_status()
        }))
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Handle client commands
                        response = await self._handle_ws_command(data)
                        await ws.send_str(json.dumps(response))
                    except Exception as e:
                        await ws.send_str(json.dumps({"error": str(e)}))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self._ws_clients.remove(ws)
            logger.info(f"WebSocket client disconnected. Total: {len(self._ws_clients)}")
        
        return ws
    
    async def _handle_ws_command(self, data: dict) -> dict:
        """Handle WebSocket command."""
        command = data.get("command")
        
        if command == "ping":
            return {"type": "pong", "timestamp": datetime.now().isoformat()}
        elif command == "status":
            return {"type": "status", "data": self._get_status()}
        elif command == "playlist":
            return {"type": "playlist", "data": self._get_playlist()}
        else:
            return {"error": f"Unknown command: {command}"}
    
    # Helper methods
    def _get_status(self) -> dict:
        """Get player status."""
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
            "current_track": self._get_current_track(),
        }
    
    def _get_playlist(self) -> dict:
        """Get playlist."""
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
    
    def _get_current_track(self) -> Optional[dict]:
        """Get current track."""
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
    
    async def start(self):
        """Start the daemon server."""
        self._running = True
        
        # Initialize audio engine
        self.audio_engine.initialize()
        
        # Start monitor thread for auto-play next
        self._start_monitor()
        
        # Setup signal handlers
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Daemon server started on http://{self.host}:{self.port}")
        
        # Keep running
        while self._running:
            await asyncio.sleep(1)
        
        # Cleanup
        await runner.cleanup()
        self.audio_engine.shutdown()
        logger.info("Daemon server stopped")
    
    async def stop(self):
        """Stop the daemon server."""
        self._running = False


async def run_daemon(
    port: int = 8080,
    host: str = "localhost",
    audio_engine: Optional[AudioEngine] = None,
    playlist: Optional[Playlist] = None,
):
    """Run the daemon server."""
    server = DaemonServer(
        audio_engine=audio_engine,
        playlist=playlist,
        port=port,
        host=host,
    )
    await server.start()
