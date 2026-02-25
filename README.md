# Music - CLI Music Player

A beautiful terminal-based music player with real-time audio visualization, customizable themes, and multiple layout options.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Features

- 🎵 **Audio Playback**: Support for MP3, FLAC, WAV, AAC, OGG, M4A formats
- 📊 **Visualizations**: 8 visualization types including spectrum, waveform, circle, stereo, mirror, oscilloscope
- 🎨 **Themes**: 5 built-in themes (Default, Neon, Minimal, Retro, Ocean)
- 📐 **Layouts**: 6 layout styles (Default, Compact, Visual, Playlist, Minimal, Split)
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

#### Playback
| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `N` | Next track |
| `P` | Previous track |
| `←/→` | Seek -10s/+10s |
| `↑/↓` | Volume down/up |

#### Controls
| Key | Action |
|-----|--------|
| `M` | Mute |
| `S` | Toggle shuffle |
| `R` | Toggle repeat |
| `T` | Switch theme |
| `V` | Next visualizer |
| `Shift+V` | Previous visualizer |
| `Ctrl+V` | Visualizer menu |
| `L` | Toggle playlist |
| `Shift+L` | Next layout |
| `Ctrl+L` | Layout menu |

#### General
| Key | Action |
|-----|--------|
| `Q` | Quit |
| `?` | Show help |

## Visualizations

The player supports 8 visualization types:

| Type | Description |
|------|-------------|
| **spectrum** | Classic frequency spectrum analyzer |
| **waveform** | Time-domain waveform display |
| **circle** | Circular/radial spectrum |
| **stereo** | Left/Right channel separation |
| **mirror** | Symmetric mirror display |
| **oscilloscope** | Retro oscilloscope style |
| **compact** | Single-line spectrum |
| **symmetry** | Center-symmetric spectrum |

Press `V` to cycle through visualizations or `Ctrl+V` to open the selection menu.

## Themes

Music player includes 5 built-in themes:

- **default**: Classic terminal theme
- **neon**: Cyberpunk neon colors
- **minimal**: Clean minimal design
- **retro**: Vintage amber monitor
- **ocean**: Deep ocean blue

Switch themes by pressing `T` or start with `music -t <theme>`.

## Layouts

Choose from 6 different layout styles:

| Layout | Description | Best For |
|--------|-------------|----------|
| **default** | Balanced view with all components | General use |
| **compact** | Minimal view without visualizer | Small terminals |
| **visual** | Maximized visualizer area | Visual experience |
| **playlist** | Playlist-focused layout | Managing libraries |
| **minimal** | Single-line display | Background playback |
| **split** | Side-by-side visualizer and playlist | Wide terminals |

Press `Shift+L` to cycle through layouts or `Ctrl+L` to open the selection menu.

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
  sensitivity: 1.0
  bar_count: 32
  smoothing: 0.3
  available_types:
    - spectrum
    - circle
    - stereo
    - mirror
    - waveform
    - oscilloscope

interface:
  layout: default
  auto_layout: true
  show_notifications: true

theme:
  name: default
```

## License

MIT License
