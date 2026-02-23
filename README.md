# Music - CLI Music Player

A beautiful terminal-based music player with real-time audio visualization and customizable themes.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Features

- 🎵 **Audio Playback**: Support for MP3, FLAC, WAV, AAC, OGG, M4A formats
- 📊 **Visualizations**: Spectrum analyzer, waveform display
- 🎨 **Themes**: 5 built-in themes (Default, Neon, Minimal, Retro, Ocean)
- 📑 **Playlist Management**: M3U/JSON playlist support, shuffle, repeat
- ⌨️ **Keyboard Controls**: Vim-style shortcuts
- 🖥️ **Terminal UI**: Rich TUI built with Textual

## Installation

### From Source

```bash
git clone <repository>
cd cli-music-player
pip install -e .
```

### Requirements

- Python 3.8+
- PortAudio (for audio playback)
  - macOS: `brew install portaudio`
  - Ubuntu/Debian: `sudo apt-get install portaudio19-dev`
  - Fedora: `sudo dnf install portaudio-devel`

## Usage

### Basic Usage

```bash
# Play a single file
music song.mp3

# Play a folder
music ~/Music/

# Play a playlist
music playlist.m3u

# Use a specific theme
music -t neon song.mp3

# Start with shuffle enabled
music -s ~/Music/
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `N` | Next track |
| `P` | Previous track |
| `←/→` | Seek -10s/+10s |
| `↑/↓` | Volume down/up |
| `M` | Mute |
| `S` | Toggle shuffle |
| `R` | Toggle repeat |
| `T` | Switch theme |
| `V` | Switch visualizer |
| `L` | Toggle playlist |
| `Q` | Quit |
| `?` | Show help |

## Themes

Music player includes 5 built-in themes:

- **default**: Classic terminal theme
- **neon**: Cyberpunk neon colors
- **minimal**: Clean minimal design
- **retro**: Vintage amber monitor
- **ocean**: Deep ocean blue

Switch themes by pressing `T` or start with `music -t <theme>`.

## Configuration

Configuration is stored in `~/.config/music/config.yaml`:

```yaml
player:
  default_volume: 70
  remember_position: true
  
visualizer:
  enabled: true
  type: spectrum
  fps: 30
  
theme:
  name: default
```

## License

MIT License
