"""Base layout interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional
from textual.containers import Container


class Layout(ABC):
    """Base class for UI layouts."""
    
    name: str = "base"
    display_name: str = "Base Layout"
    description: str = "Base layout class"
    
    @property
    @abstractmethod
    def min_height(self) -> int:
        """Minimum terminal height required for this layout."""
        pass
    
    @property
    @abstractmethod
    def min_width(self) -> int:
        """Minimum terminal width required for this layout."""
        pass
    
    @abstractmethod
    def compose(self, screen) -> List:
        """Compose the layout widgets for the screen.
        
        Returns a list of widgets/containers to add to the screen.
        """
        pass
    
    def should_use(self, width: int, height: int) -> bool:
        """Check if this layout can be used with given terminal dimensions."""
        return width >= self.min_width and height >= self.min_height


class LayoutManager:
    """Manages available layouts and switching."""
    
    def __init__(self):
        self._layouts: Dict[str, Layout] = {}
        self._current: Optional[Layout] = None
        self._current_name: str = "default"
        self._register_builtin_layouts()
    
    def _register_builtin_layouts(self):
        """Register all built-in layouts."""
        # Import here to avoid circular imports
        from .default import DefaultLayout
        from .compact import CompactLayout
        from .visual import VisualLayout
        from .playlist import PlaylistLayout
        from .minimal import MinimalLayout
        from .split import SplitLayout
        
        layouts = [
            DefaultLayout(),
            CompactLayout(),
            VisualLayout(),
            PlaylistLayout(),
            MinimalLayout(),
            SplitLayout(),
        ]
        
        for layout in layouts:
            self._layouts[layout.name] = layout
        
        self._current = self._layouts.get("default")
    
    def list_layouts(self) -> List[str]:
        """List all available layout names."""
        return list(self._layouts.keys())
    
    def get_layout(self, name: str) -> Optional[Layout]:
        """Get layout by name."""
        return self._layouts.get(name)
    
    def get_layout_info(self) -> List[dict]:
        """Get info about all layouts."""
        return [
            {
                "name": layout.name,
                "display_name": layout.display_name,
                "description": layout.description,
                "min_width": layout.min_width,
                "min_height": layout.min_height,
            }
            for layout in self._layouts.values()
        ]
    
    @property
    def current(self) -> Optional[Layout]:
        """Get current layout."""
        return self._current
    
    @property
    def current_name(self) -> str:
        """Get current layout name."""
        return self._current_name
    
    def switch_to(self, name: str) -> bool:
        """Switch to layout by name."""
        if name in self._layouts:
            self._current = self._layouts[name]
            self._current_name = name
            return True
        return False
    
    def next(self, reverse: bool = False) -> str:
        """Switch to next layout, returns new name."""
        names = self.list_layouts()
        if not names:
            return self._current_name
        
        try:
            current_idx = names.index(self._current_name)
        except ValueError:
            current_idx = 0
        
        if reverse:
            next_idx = (current_idx - 1) % len(names)
        else:
            next_idx = (current_idx + 1) % len(names)
        
        new_name = names[next_idx]
        self.switch_to(new_name)
        return new_name
    
    def auto_select(self, width: int, height: int, compact_threshold: int = 20) -> str:
        """Automatically select best layout for terminal size."""
        # Check if we should use compact layout
        if height < compact_threshold:
            if "compact" in self._layouts:
                self.switch_to("compact")
                return "compact"
        
        # Check if we can use split layout (wide terminal)
        if width >= 120 and "split" in self._layouts:
            self.switch_to("split")
            return "split"
        
        # Default to default layout
        if "default" in self._layouts:
            self.switch_to("default")
            return "default"
        
        return self._current_name


# Global layout manager instance
layout_manager = LayoutManager()
