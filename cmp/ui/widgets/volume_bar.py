"""Volume bar widget."""
from textual.widgets import Static
from textual.reactive import reactive


class VolumeBar(Static):
    """A volume bar widget."""
    
    volume = reactive(70)
    muted = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filled_char = "▓"
        self.empty_char = "▒"
        self.mute_char = "🔇"
    
    def set_chars(self, filled: str, empty: str, mute: str):
        """Set volume bar characters."""
        self.filled_char = filled
        self.empty_char = empty
        self.mute_char = mute
    
    def watch_volume(self, volume: int):
        """Update display when volume changes."""
        self.update_display()
    
    def watch_muted(self, muted: bool):
        """Update display when mute state changes."""
        self.update_display()
    
    def update_display(self):
        """Update the volume bar display."""
        width = self.size.width if self.size else 20
        if width <= 0:
            return
        
        if self.muted:
            self.update(f"{self.mute_char} MUTE")
            return
        
        percentage = max(0, min(100, self.volume))
        filled_width = int((width - 5) * percentage / 100)
        empty_width = (width - 5) - filled_width
        
        bar = self.filled_char * filled_width + self.empty_char * empty_width
        self.update(f"Vol:{bar} {percentage}%")
    
    def on_mount(self):
        """Initialize on mount."""
        self.update_display()
    
    def on_resize(self):
        """Update on resize."""
        self.update_display()
