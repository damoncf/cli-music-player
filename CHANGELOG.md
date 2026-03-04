# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-04

### Added
- Initial release
- TUI music player with visualizations
- 8 visualization types (spectrum, waveform, circle, stereo, mirror, oscilloscope, compact, symmetry)
- 5 built-in themes (default, neon, minimal, retro, ocean)
- 6 layout styles (default, compact, visual, playlist, minimal, split)
- Playlist management (M3U/JSON support)
- MCP server for AI agent control
- HTTP API daemon mode
- Keyboard shortcuts (Vim-style)
- Audio format support: MP3, FLAC, WAV, AAC, OGG, M4A

### Fixed
- MCP command parsing bug (paths argument conflict)

---

## [0.2.0] - Planned

### High Priority
- [ ] **Lyrics Support** - Display synchronized lyrics from LRC files
- [ ] **Search** - Search within playlist by title/artist/album
- [ ] **Queue Management** - Temporary play queue separate from playlist
- [ ] **Crossfade** - Smooth transition between tracks

### Medium Priority
- [ ] **Web UI** - Browser-based remote control interface
- [ ] **Equalizer** - Audio EQ with presets
- [ ] **Play History** - Track recently played songs
- [ ] **Favorites** - Mark and quickly access favorite tracks
- [ ] **Metadata Editor** - Edit song metadata

### Low Priority
- [ ] **Smart Playlists** - Auto-generate playlists based on rules
- [ ] **Streaming** - Support network streams (HTTP, Icecast)
- [ ] **Plugins** - Plugin system for extensions
- [ ] **More Formats** - DSD, APE, WavPack support
- [ ] **Last.fm Integration** - Scrobble support

---

## Version Naming Convention

- **0.x.0** - Minor version with new features
- **0.1.x** - Patch version with bug fixes only