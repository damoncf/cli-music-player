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

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `N` | Next |
| `P` | Previous |
| `←/→` | Seek -10s/+10s |
| `↑/↓` | Volume -/+ |
| `M` | Mute |
| `S` | Shuffle |
| `R` | Repeat (none/all/one) |
| `T` | Switch theme |
| `V` | Switch visualizer |
| `L` | Toggle playlist |
| `Q` | Quit |
| `?` | Help |

## Themes

Built-in themes: `default`, `neon`, `minimal`, `retro`, `ocean`

Switch with `T` key or `music -t <theme>`

## Configuration

Edit `~/.config/music/config.yaml` to customize settings.
