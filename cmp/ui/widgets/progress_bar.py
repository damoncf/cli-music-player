"""Progress bar widget."""
from textual.widgets import Static
from textual.reactive import reactive


class ProgressBar(Static):
    """A progress bar widget."""
    
    progress = reactive(0.0)
    total = reactive(100.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filled_char = "█"
        self.empty_char = "░"
    
    def set_chars(self, filled: str, empty: str):
        """Set progress bar characters."""
        self.filled_char = filled
        self.empty_char = empty
    
    def watch_progress(self, progress: float):
        """Update display when progress changes."""
        self.update_display()
    
    def update_display(self):
        """Update the progress bar display."""
        width = self.size.width if self.size else 40
        if width <= 0:
            return
        
        percentage = self.progress / self.total if self.total > 0 else 0
        percentage = max(0.0, min(1.0, percentage))
        
        filled_width = int(width * percentage)
        empty_width = width - filled_width
        
        bar = self.filled_char * filled_width + self.empty_char * empty_width
        self.update(bar)
    
    def on_mount(self):
        """Initialize on mount."""
        self.update_display()
    
    def on_resize(self):
        """Update on resize."""
        self.update_display()
