"""Theme management."""
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import yaml


@dataclass
class ThemeColors:
    """Theme color definitions."""
    background: str = "#000000"
    foreground: str = "#ffffff"
    primary: str = "#00aa00"
    secondary: str = "#0088ff"
    accent: str = "#ffaa00"
    playing: str = "#00ff00"
    paused: str = "#ffff00"
    stopped: str = "#ff0000"
    progress_filled: str = "#00aa00"
    progress_empty: str = "#444444"
    volume_filled: str = "#0088ff"
    volume_empty: str = "#444444"
    playlist_selected: str = "#1a1a1a"
    playlist_current: str = "#00ff00"
    visualizer_primary: str = "#00ff00"
    visualizer_secondary: str = "#0088ff"


@dataclass
class ThemeChars:
    """Theme character definitions."""
    progress_filled: str = "█"
    progress_empty: str = "░"
    volume_filled: str = "▓"
    volume_empty: str = "▒"
    play: str = "▶"
    pause: str = "⏸"
    stop: str = "⏹"
    next: str = "⏭"
    prev: str = "⏮"
    shuffle: str = "🔀"
    repeat: str = "🔁"
    repeat_one: str = "🔂"


@dataclass
class Theme:
    """Complete theme definition."""
    name: str = "default"
    display_name: str = "Default"
    description: str = "Default terminal theme"
    colors: ThemeColors = field(default_factory=ThemeColors)
    chars: ThemeChars = field(default_factory=ThemeChars)
    
    # Visualizer settings
    visualizer_bar_count: int = 32
    visualizer_smoothing: float = 0.3


class ThemeManager:
    """Manages themes."""
    
    def __init__(self):
        self._themes: Dict[str, Theme] = {}
        self._current: Optional[Theme] = None
        self._builtin_themes_dir = Path(__file__).parent / "builtin"
        self._user_themes_dir = Path.home() / ".config" / "cmp" / "themes"
        self._load_builtin_themes()
    
    def _load_builtin_themes(self):
        """Load built-in themes."""
        # Default theme
        self._themes["default"] = Theme(
            name="default",
            display_name="Default",
            description="Classic terminal theme",
            colors=ThemeColors(),
            chars=ThemeChars()
        )
        
        # Neon theme
        neon_colors = ThemeColors(
            background="#0a0a0f",
            foreground="#00ff9d",
            primary="#00ff9d",
            secondary="#ff00ff",
            accent="#00ffff",
            playing="#00ff9d",
            paused="#ffff00",
            progress_filled="#00ff9d",
            volume_filled="#00ffff",
            visualizer_primary="#00ff9d",
            visualizer_secondary="#ff00ff"
        )
        self._themes["neon"] = Theme(
            name="neon",
            display_name="Neon",
            description="Cyberpunk neon theme",
            colors=neon_colors
        )
        
        # Minimal theme
        minimal_colors = ThemeColors(
            background="#000000",
            foreground="#aaaaaa",
            primary="#ffffff",
            secondary="#666666",
            accent="#ffffff",
            playing="#ffffff",
            progress_filled="█",
            progress_empty="░"
        )
        self._themes["minimal"] = Theme(
            name="minimal",
            display_name="Minimal",
            description="Clean minimal theme",
            colors=minimal_colors
        )
        
        # Retro theme (amber monitor)
        retro_colors = ThemeColors(
            background="#1a1200",
            foreground="#ffb000",
            primary="#ffb000",
            secondary="#ff8000",
            accent="#ff6600",
            playing="#ffb000",
            paused="#ff8000",
            progress_filled="#ffb000",
            volume_filled="#ff8000",
            visualizer_primary="#ffb000",
            visualizer_secondary="#ff8000"
        )
        retro_chars = ThemeChars(
            progress_filled="=",
            progress_empty="-",
            volume_filled="#",
            volume_empty="-"
        )
        self._themes["retro"] = Theme(
            name="retro",
            display_name="Retro",
            description="Vintage amber monitor theme",
            colors=retro_colors,
            chars=retro_chars
        )
        
        # Ocean theme
        ocean_colors = ThemeColors(
            background="#001122",
            foreground="#66ccff",
            primary="#0088cc",
            secondary="#00aadd",
            accent="#00ffff",
            playing="#00ccff",
            paused="#88ccff",
            progress_filled="#0088cc",
            volume_filled="#00aadd",
            visualizer_primary="#00ccff",
            visualizer_secondary="#0088cc"
        )
        self._themes["ocean"] = Theme(
            name="ocean",
            display_name="Ocean",
            description="Deep ocean blue theme",
            colors=ocean_colors
        )
        
        # Set default
        self._current = self._themes["default"]
    
    def list_themes(self) -> List[Theme]:
        """List all available themes."""
        return list(self._themes.values())
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self._themes.get(name)
    
    @property
    def current(self) -> Theme:
        """Get current theme."""
        return self._current or self._themes["default"]
    
    def apply_theme(self, name: str) -> bool:
        """Apply theme by name. Returns success."""
        if name in self._themes:
            self._current = self._themes[name]
            return True
        return False
    
    def load_theme_file(self, path: Path) -> Optional[Theme]:
        """Load theme from file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            theme = Theme(
                name=data.get("name", path.stem),
                display_name=data.get("display_name", path.stem),
                description=data.get("description", ""),
            )
            
            # Load colors
            if "colors" in data:
                for key, value in data["colors"].items():
                    if hasattr(theme.colors, key):
                        setattr(theme.colors, key, value)
            
            # Load chars
            if "chars" in data:
                for key, value in data["chars"].items():
                    if hasattr(theme.chars, key):
                        setattr(theme.chars, key, value)
            
            self._themes[theme.name] = theme
            return theme
        except Exception as e:
            print(f"Error loading theme: {e}")
            return None
    
    def save_theme(self, theme: Theme, path: Path):
        """Save theme to file."""
        data = {
            "name": theme.name,
            "display_name": theme.display_name,
            "description": theme.description,
            "colors": theme.colors.__dict__,
            "chars": theme.chars.__dict__
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# Global theme manager instance
theme_manager = ThemeManager()
