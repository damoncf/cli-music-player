"""Configuration settings for CMP."""
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
import yaml
import os


class PlayerConfig(BaseModel):
    """Player configuration."""
    default_volume: int = Field(default=70, ge=0, le=100)
    remember_position: bool = True
    auto_play: bool = False
    fade_in_out: bool = False


class PlaylistConfig(BaseModel):
    """Playlist configuration."""
    default_sort: str = "name"
    recursive_add: bool = True
    save_on_exit: bool = True
    history_size: int = 100
    filters: dict = Field(default_factory=lambda: {
        "include": ["*.mp3", "*.flac", "*.wav", "*.aac", "*.ogg", "*.m4a", "*.wma"],
        "exclude": ["*temp*", "*cache*", ".*"]
    })


class VisualizerConfig(BaseModel):
    """Visualizer configuration."""
    enabled: bool = True
    type: str = "spectrum"
    fps: int = 30
    sensitivity: float = Field(default=1.0, ge=0.1, le=3.0)
    bar_count: int = Field(default=32, ge=8, le=128)
    smoothing: float = Field(default=0.3, ge=0.0, le=1.0)


class ThemeConfig(BaseModel):
    """Theme configuration."""
    name: str = "default"
    custom_path: Optional[str] = None


class KeybindingsConfig(BaseModel):
    """Keybindings configuration."""
    quit: str = "q"
    play_pause: str = "space"
    next: str = "n"
    prev: str = "p"
    volume_up: str = "up"
    volume_down: str = "down"
    mute: str = "m"
    shuffle: str = "s"
    repeat: str = "r"
    theme: str = "t"
    visualizer: str = "v"
    playlist: str = "l"
    help: str = "?"


class InterfaceConfig(BaseModel):
    """Interface configuration."""
    show_notifications: bool = True
    compact_mode: bool = False


class Config(BaseModel):
    """Main configuration."""
    version: str = "1.0"
    player: PlayerConfig = Field(default_factory=PlayerConfig)
    playlist: PlaylistConfig = Field(default_factory=PlaylistConfig)
    visualizer: VisualizerConfig = Field(default_factory=VisualizerConfig)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    keybindings: KeybindingsConfig = Field(default_factory=KeybindingsConfig)
    interface: InterfaceConfig = Field(default_factory=InterfaceConfig)


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "cmp"
        self.config_file = self.config_dir / "config.yaml"
        self.cache_dir = Path.home() / ".cache" / "cmp"
        self._config: Optional[Config] = None
    
    @property
    def config(self) -> Config:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def ensure_directories(self):
        """Ensure config and cache directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "playlists").mkdir(exist_ok=True)
        (self.config_dir / "themes").mkdir(exist_ok=True)
    
    def load(self) -> Config:
        """Load configuration from file."""
        self.ensure_directories()
        
        if not self.config_file.exists():
            config = Config()
            self.save(config)
            return config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return Config(**data)
        except Exception:
            # Backup corrupt config and create default
            backup = self.config_file.with_suffix(".yaml.backup")
            self.config_file.rename(backup)
            config = Config()
            self.save(config)
            return config
    
    def save(self, config: Optional[Config] = None):
        """Save configuration to file."""
        config = config or self._config
        if config is None:
            return
        
        self.ensure_directories()
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, allow_unicode=True)
    
    def reset(self) -> Config:
        """Reset to default configuration."""
        config = Config()
        self._config = config
        self.save(config)
        return config


# Global config manager instance
config_manager = ConfigManager()
