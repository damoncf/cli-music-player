"""UI Layouts."""
from .base import Layout, LayoutManager
from .default import DefaultLayout
from .compact import CompactLayout
from .visual import VisualLayout
from .playlist import PlaylistLayout
from .minimal import MinimalLayout
from .split import SplitLayout

__all__ = [
    "Layout",
    "LayoutManager", 
    "DefaultLayout",
    "CompactLayout",
    "VisualLayout",
    "PlaylistLayout",
    "MinimalLayout",
    "SplitLayout",
]
