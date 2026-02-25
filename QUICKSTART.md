# Quick Start Guide

## Installation

### 1. Install System Dependencies

**macOS:**
```bash
brew install portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Fedora:**
```bash
sudo dnf install portaudio-devel
```

### 2. Install Music Player

```bash
cd ~/works2/cli-music-player
pip install -e .
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

### 3. Run Music Player

```bash
# Play a single file
music song.mp3

# Play a folder
music ~/Music/

# Play with neon theme
music -t neon song.mp3

# Enable shuffle
music -s ~/Music/
```

## Controls

### Playback
| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `N` | Next |
| `P` | Previous |
| `←/→` | Seek -10s/+10s |
| `↑/↓` | Volume -/+ |

### Visualizations
| Key | Action |
|-----|--------|
| `V` | Next visualizer |
| `Shift+V` | Previous visualizer |
| `Ctrl+V` | Visualizer menu |

**Available Visualizers:**
- `spectrum` - Classic frequency bars
- `circle` - Circular radial display
- `stereo` - Left/Right channel separation
- `mirror` - Symmetric mirror display
- `oscilloscope` - Retro oscilloscope style
- `waveform` - Time-domain waveform
- `symmetry` - Center-symmetric spectrum
- `compact` - Single-line spectrum

### Layouts
| Key | Action |
|-----|--------|
| `Shift+L` | Next layout |
| `Ctrl+L` | Layout menu |

**Available Layouts:**
- `default` - Balanced view
- `compact` - Small terminal optimized
- `visual` - Maximized visualizer
- `playlist` - Playlist-focused
- `minimal` - Single-line display
- `split` - Wide screen side-by-side

### Other Controls
| Key | Action |
|-----|--------|
| `M` | Mute |
| `S` | Shuffle |
| `R` | Repeat (none/all/one) |
| `T` | Switch theme |
| `L` | Toggle playlist |
| `Q` | Quit |
| `?` | Help |

## Themes

Built-in themes: `default`, `neon`, `minimal`, `retro`, `ocean`

Switch with `T` key or `music -t <theme>`

## Configuration

Edit `~/.config/music/config.yaml` to customize settings:

```yaml
player:
  default_volume: 70
  
visualizer:
  type: spectrum  # or circle, stereo, mirror, etc.
  fps: 30
  
interface:
  layout: default  # or compact, visual, playlist, etc.
  auto_layout: true
```

## Tips

1. **Small Terminal?** Use `compact` layout or press `Ctrl+L` to select it
2. **Want Visuals?** Use `visual` layout for maximum visualizer area
3. **Managing Playlist?** Use `playlist` layout for easy track selection
4. **Background Play?** Use `minimal` layout for single-line display
5. **Wide Screen?** Use `split` layout for visualizer + playlist side-by-side
