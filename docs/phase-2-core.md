# Phase 2: Core Stabilization & AI Agent Integration

## Overview

Phase 2 focuses on two primary objectives:
1. **Core Stability**: Hardening the existing functionality, improving error handling, and ensuring reliable operation
2. **AI Agent Integration**: Making the music player accessible and controllable by AI agents through standardized protocols (MCP)

---

## 1. Core Stability Requirements

### 1.1 Error Handling & Resilience

| Component | Current State | Target State |
|-----------|--------------|--------------|
| Audio Engine | Basic error handling | Graceful degradation with auto-recovery |
| Visualizer | May crash on buffer underrun | Self-healing with fallback modes |
| Playlist | Simple file loading | Corruption-resistant with validation |
| Config | Basic YAML parsing | Schema validation with migration |
| Theme System | Load-time validation | Runtime fallback + hot-reload |

**Requirements:**
- [ ] Implement circuit breaker pattern for audio device errors
- [ ] Add automatic retry with exponential backoff for file operations
- [ ] Create graceful degradation (e.g., disable visualizer if CPU > 80%)
- [ ] Implement config file backup and automatic recovery
- [ ] Add comprehensive logging with structured output (JSON)

### 1.2 State Management

**Current Issue**: State is distributed across multiple modules without a single source of truth.

**Requirements:**
- [ ] Implement centralized state store (reactive pattern)
- [ ] Add state persistence (save/restore player state on crash)
- [ ] Create state snapshots for undo/redo functionality
- [ ] Implement state validation guards

```python
# Target API
class PlayerState:
    playback: PlaybackState
    playlist: PlaylistState
    config: ConfigState
    visualizer: VisualizerState
    
    def snapshot(self) -> StateSnapshot
    def restore(self, snapshot: StateSnapshot)
    def subscribe(self, callback: Callable[[StateChange], None])
```

### 1.3 Testing & Quality

**Requirements:**
- [ ] Achieve >80% code coverage
- [ ] Add integration tests for audio pipeline
- [ ] Create mock audio backend for headless testing
- [ ] Add property-based testing for playlist operations
- [ ] Implement fuzzing for metadata parsing
- [ ] Add performance benchmarks (startup time, memory usage)

### 1.4 Documentation

**Requirements:**
- [ ] Auto-generated API documentation from docstrings
- [ ] Architecture decision records (ADRs)
- [ ] Troubleshooting guide with common errors
- [ ] Contributing guidelines

---

## 2. AI Agent Integration (MCP Protocol)

### 2.1 MCP (Model Context Protocol) Overview

MCP is a protocol that allows AI assistants to interact with external tools through a standardized interface. Implementing MCP will enable:
- AI agents to control music playback
- Context-aware music recommendations
- Natural language playlist management
- Automated music organization

### 2.2 MCP Server Implementation

**Requirements:**
- [ ] Implement MCP server with stdio and HTTP transports
- [ ] Expose all player functionality as MCP tools
- [ ] Provide resource endpoints for current state
- [ ] Support prompts for common workflows

```python
# MCP Tools to expose
class MusicPlayerMCPServer:
    # Playback control tools
    @tool
    async def play(self, track_id: str | None = None) -> PlaybackResult
    
    @tool
    async def pause(self) -> PlaybackResult
    
    @tool
    async def stop(self) -> PlaybackResult
    
    @tool
    async def next_track(self) -> TrackResult
    
    @tool
    async def previous_track(self) -> TrackResult
    
    @tool
    async def seek(self, position_seconds: float) -> PlaybackResult
    
    @tool
    async def set_volume(self, volume: int) -> VolumeResult
    
    @tool
    async def set_shuffle(self, enabled: bool) -> ModeResult
    
    @tool
    async def set_repeat(self, mode: Literal["none", "all", "one"]) -> ModeResult
    
    # Playlist management tools
    @tool
    async def get_playlist(self) -> PlaylistResult
    
    @tool
    async def add_to_playlist(self, paths: list[str]) -> PlaylistResult
    
    @tool
    async def remove_from_playlist(self, indices: list[int]) -> PlaylistResult
    
    @tool
    async def clear_playlist(self) -> PlaylistResult
    
    @tool
    async def sort_playlist(self, by: str, reverse: bool = False) -> PlaylistResult
    
    @tool
    async def search_playlist(self, query: str) -> SearchResult
    
    @tool
    async def jump_to_track(self, index: int) -> TrackResult
    
    @tool
    async def create_playlist(self, name: str, tracks: list[str]) -> PlaylistResult
    
    @tool
    async def save_playlist(self, path: str, format: Literal["m3u", "json"]) -> FileResult
    
    @tool
    async def load_playlist(self, path: str) -> PlaylistResult
    
    # Visualizer tools
    @tool
    async def set_visualizer(self, type: str) -> VisualizerResult
    
    @tool
    async def list_visualizers(self) -> list[VisualizerInfo]
    
    @tool
    async def set_visualizer_sensitivity(self, sensitivity: float) -> VisualizerResult
    
    @tool
    async def enable_visualizer(self, enabled: bool) -> VisualizerResult
    
    # Theme tools
    @tool
    async def set_theme(self, name: str) -> ThemeResult
    
    @tool
    async def list_themes(self) -> list[ThemeInfo]
    
    @tool
    async def get_current_theme(self) -> ThemeInfo
    
    # Layout tools
    @tool
    async def set_layout(self, name: str) -> LayoutResult
    
    @tool
    async def list_layouts(self) -> list[LayoutInfo]
    
    # Configuration tools
    @tool
    async def get_config(self) -> ConfigResult
    
    @tool
    async def update_config(self, updates: dict) -> ConfigResult
    
    @tool
    async def reset_config(self) -> ConfigResult
    
    # Metadata and info tools
    @tool
    async def get_current_track(self) -> TrackInfo | None
    
    @tool
    async def get_player_status(self) -> PlayerStatus
    
    @tool
    async def get_library_stats(self) -> LibraryStats
    
    @tool
    async def extract_metadata(self, path: str) -> MetadataResult
```

### 2.3 MCP Resources

**Requirements:**
- [ ] Expose current playback state as a resource
- [ ] Provide playlist as a queryable resource
- [ ] Offer configuration as a resource
- [ ] Support resource subscriptions for real-time updates

```python
# MCP Resources
resources = {
    "player://status": Current playback state,
    "player://playlist": Current playlist with tracks,
    "player://queue": Upcoming tracks,
    "player://history": Recently played tracks,
    "player://config": Current configuration,
    "player://themes": Available themes,
    "player://visualizers": Available visualizers,
    "player://layouts": Available layouts,
}
```

### 2.4 MCP Prompts

**Requirements:**
- [ ] Create prompts for common AI-assisted workflows
- [ ] Support parameterized prompts

```python
# Example MCP Prompts
prompts = {
    "create_focus_playlist": """
    Create a playlist for focused work session.
    Parameters: duration (minutes), intensity (low/medium/high)
    """,
    
    "analyze_listening_habits": """
    Analyze my recent listening history and suggest new tracks.
    """,
    
    "fix_metadata": """
    Find and fix metadata issues in my music library.
    """,
    
    "optimize_settings": """
    Optimize player settings for my current system.
    """,
}
```

---

## 3. Programmatic API Enhancements

### 3.1 Async API

**Requirements:**
- [ ] Convert core API to async/await pattern
- [ ] Add asyncio-compatible event handling
- [ ] Support concurrent operations

```python
# Target API
from cmp import MusicPlayer

async with MusicPlayer() as player:
    await player.playlist.add("~/Music/")
    await player.playback.play()
    
    # Subscribe to events
    async for event in player.events:
        if isinstance(event, TrackChanged):
            print(f"Now playing: {event.track.title}")
```

### 3.2 Type Safety

**Requirements:**
- [ ] Full type annotations with Pydantic models
- [ ] Runtime type validation
- [ ] Generated TypeScript types for web clients

```python
class Track(BaseModel):
    id: str
    path: Path
    title: str
    artist: str
    album: str | None
    duration: float
    metadata: AudioMetadata

class PlaybackState(BaseModel):
    status: Literal["idle", "playing", "paused", "stopped"]
    current_track: Track | None
    position: float
    volume: int
    shuffle: bool
    repeat: Literal["none", "all", "one"]
```

### 3.3 Batch Operations

**Requirements:**
- [ ] Support batch playlist modifications
- [ ] Add bulk metadata operations
- [ ] Implement transaction-like semantics

```python
# Batch operations
async with player.playlist.batch() as batch:
    batch.add("~/Music/Album1/")
    batch.add("~/Music/Album2/")
    batch.remove([0, 1, 2])
    batch.sort(by="artist")
# All operations applied atomically
```

---

## 4. Headless Mode

### 4.1 Daemon/Server Mode

**Requirements:**
- [ ] Run player as background daemon
- [ ] HTTP/WebSocket API for remote control
- [ ] Support multiple simultaneous clients
- [ ] Add authentication/authorization

```python
# Headless mode
uv run python -m cmp --daemon --port 8080 --mcp

# Client usage
uv run python -m cmp client play ~/Music/song.mp3
uv run python -m cmp client status
```

### 4.2 CLI Improvements

**Requirements:**
- [ ] Non-interactive mode for scripting
- [ ] JSON output format for all commands
- [ ] Exit codes for automation
- [ ] Pipe support for playlist operations

```bash
# JSON output for scripting
cmp --json status | jq '.current_track.title'

# Pipe support
cmp search "rock" | cmp add -

# Non-interactive
cmp --no-ui play ~/Music/album.mp3
```

---

## 5. Event System Enhancements

### 5.1 WebSocket Events

**Requirements:**
- [ ] WebSocket endpoint for real-time events
- [ ] Event filtering by type
- [ ] Event replay capability

```json
{
  "type": "playback.position_changed",
  "timestamp": "2026-03-03T21:55:35Z",
  "data": {
    "position": 123.45,
    "duration": 234.56,
    "percentage": 0.526
  }
}
```

### 5.2 Event Persistence

**Requirements:**
- [ ] Persist events to SQLite for history
- [ ] Queryable event log
- [ ] Event-driven analytics

---

## 6. Configuration Management

### 6.1 Schema Versioning

**Requirements:**
- [ ] Version config schema
- [ ] Automatic migration between versions
- [ ] Config validation with detailed errors

### 6.2 Environment Variables

**Requirements:**
- [ ] Support all config via env vars (CMP_*)
- [ ] Secret management for API keys (future)
- [ ] Docker-friendly configuration

---

## 7. Implementation Plan

### Phase 2A: Core Stabilization (Week 1-2)
- [ ] Implement centralized state management
- [ ] Add comprehensive error handling
- [ ] Create mock audio backend for testing
- [ ] Add structured logging
- [ ] Write integration tests

### Phase 2B: Async API (Week 2-3)
- [ ] Convert core components to async
- [ ] Implement Pydantic models for all types
- [ ] Add batch operations support
- [ ] Create programmatic API layer

### Phase 2C: MCP Server (Week 3-4)
- [ ] Implement MCP protocol handlers
- [ ] Expose all tools via MCP
- [ ] Add MCP resources
- [ ] Create MCP prompts
- [ ] Test with Claude Desktop

### Phase 2D: Headless & CLI (Week 4-5)
- [ ] Implement daemon mode
- [ ] Add HTTP/WebSocket API
- [ ] Improve CLI with JSON output
- [ ] Add event persistence

### Phase 2E: Documentation & Polish (Week 5-6)
- [ ] Write MCP integration guide
- [ ] Create AI agent examples
- [ ] Performance optimization
- [ ] Release Phase 2

---

## 8. MCP Use Cases

### 8.1 Natural Language Control

```
User: "Play some jazz from the 50s"
AI: Uses MCP tools to search library, create playlist, and play

User: "Make a 30-minute focus playlist"
AI: Selects appropriate tracks, sets timer, enables minimal layout
```

### 8.2 Smart Playlists

```
User: "Create a workout playlist with high-energy songs"
AI: Analyzes metadata/BPM, filters tracks, creates playlist

User: "Find songs similar to this one"
AI: Uses audio analysis to find similar tracks
```

### 8.3 Automated Organization

```
User: "Fix the metadata in my Downloads/Music folder"
AI: Scans files, identifies issues, suggests fixes, applies changes

User: "Organize my library by genre and year"
AI: Creates folder structure, moves files, updates playlists
```

### 8.4 System Integration

```
# Home automation integration
When meeting starts → Pause music
When focus mode enabled → Enable minimal layout, play lo-fi
When workout detected → Switch to high-energy playlist
```

---

## 9. Security Considerations

- [ ] Input validation on all MCP tool parameters
- [ ] Path traversal protection for file operations
- [ ] Rate limiting for MCP requests
- [ ] Optional authentication for remote access
- [ ] Audit logging for sensitive operations

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Test Coverage | >80% |
| CI/CD Pipeline | <5 min build |
| MCP Tool Response Time | <100ms |
| Daemon Memory Usage | <50MB |
| API Uptime (daemon) | 99.9% |
| Error Recovery Rate | >95% |

---

## Appendix: MCP Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Example MCP Servers](https://github.com/modelcontextprotocol/servers)
