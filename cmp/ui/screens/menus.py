"""Menu screens for visualizer and layout selection."""
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Static
from textual.reactive import reactive

from ...visualizer.manager import visualizer_manager
from ...ui.layouts.base import layout_manager


class VisualizerMenu(Screen):
    """Menu for selecting visualizer type."""
    
    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]
    
    CSS = """
    .menu-container {
        width: 50;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    .menu-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    .menu-item {
        padding: 0 1;
        height: 1;
    }
    .menu-item:hover {
        background: $primary 10%;
    }
    .menu-item.selected {
        background: $primary;
        color: $text;
    }
    .menu-item-indicator {
        width: 3;
    }
    .menu-buttons {
        padding-top: 1;
        height: auto;
        content-align: center middle;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_index = 0
        self.visualizers = visualizer_manager.list_visualizers()
        try:
            self.selected_index = self.visualizers.index(visualizer_manager.current_name)
        except ValueError:
            self.selected_index = 0
    
    def compose(self):
        with Container(classes="menu-container"):
            yield Label("Select Visualizer", classes="menu-title")
            
            for i, viz_name in enumerate(self.visualizers):
                indicator = "●" if i == self.selected_index else "○"
                css_class = "menu-item selected" if i == self.selected_index else "menu-item"
                yield Horizontal(
                    Label(indicator, classes="menu-item-indicator"),
                    Label(viz_name, classes="menu-item-name"),
                    classes=css_class,
                    id=f"viz-item-{i}"
                )
            
            with Horizontal(classes="menu-buttons"):
                yield Button("Select", id="btn-select")
                yield Button("Cancel", id="btn-cancel")
    
    def on_mount(self):
        self._update_highlight()
    
    def _update_highlight(self):
        for i, viz_name in enumerate(self.visualizers):
            indicator = "●" if i == self.selected_index else "○"
            try:
                row = self.query_one(f"#viz-item-{i}", Horizontal)
                row.query_one(".menu-item-indicator", Label).update(indicator)
                if i == self.selected_index:
                    row.add_class("selected")
                else:
                    row.remove_class("selected")
            except Exception:
                pass
    
    def action_close(self):
        self.dismiss(None)
    
    def on_button_pressed(self, event):
        if event.button.id == "btn-select":
            selected_viz = self.visualizers[self.selected_index]
            visualizer_manager.switch_to(selected_viz)
            self.dismiss(selected_viz)
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
    
    def key_up(self):
        self.selected_index = (self.selected_index - 1) % len(self.visualizers)
        self._update_highlight()
    
    def key_down(self):
        self.selected_index = (self.selected_index + 1) % len(self.visualizers)
        self._update_highlight()
    
    def key_enter(self):
        selected_viz = self.visualizers[self.selected_index]
        visualizer_manager.switch_to(selected_viz)
        self.dismiss(selected_viz)


class LayoutMenu(Screen):
    """Menu for selecting layout."""
    
    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]
    
    CSS = """
    .menu-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    .menu-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    .menu-item {
        padding: 0 1;
        height: 2;
    }
    .menu-item:hover {
        background: $primary 10%;
    }
    .menu-item.selected {
        background: $primary;
        color: $text;
    }
    .menu-item-indicator {
        width: 3;
    }
    .menu-item-info {
        text-style: dim;
    }
    .menu-buttons {
        padding-top: 1;
        height: auto;
        content-align: center middle;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_index = 0
        self.layouts = layout_manager.get_layout_info()
        try:
            self.selected_index = next(
                (i for i, l in enumerate(self.layouts) if l["name"] == layout_manager.current_name),
                0
            )
        except ValueError:
            self.selected_index = 0
    
    def compose(self):
        with Container(classes="menu-container"):
            yield Label("Select Layout", classes="menu-title")
            
            for i, layout_info in enumerate(self.layouts):
                indicator = "●" if i == self.selected_index else "○"
                css_class = "menu-item selected" if i == self.selected_index else "menu-item"
                yield Horizontal(
                    Label(indicator, classes="menu-item-indicator"),
                    Vertical(
                        Label(layout_info["display_name"], classes="menu-item-name"),
                        Label(layout_info["description"], classes="menu-item-info"),
                    ),
                    classes=css_class,
                    id=f"layout-item-{i}"
                )
            
            with Horizontal(classes="menu-buttons"):
                yield Button("Select", id="btn-select")
                yield Button("Cancel", id="btn-cancel")
    
    def on_mount(self):
        self._update_highlight()
    
    def _update_highlight(self):
        for i in range(len(self.layouts)):
            indicator = "●" if i == self.selected_index else "○"
            try:
                row = self.query_one(f"#layout-item-{i}", Horizontal)
                row.query_one(".menu-item-indicator", Label).update(indicator)
                if i == self.selected_index:
                    row.add_class("selected")
                else:
                    row.remove_class("selected")
            except Exception:
                pass
    
    def action_close(self):
        self.dismiss(None)
    
    def on_button_pressed(self, event):
        if event.button.id == "btn-select":
            selected_layout = self.layouts[self.selected_index]["name"]
            self.dismiss(selected_layout)
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
    
    def key_up(self):
        self.selected_index = (self.selected_index - 1) % len(self.layouts)
        self._update_highlight()
    
    def key_down(self):
        self.selected_index = (self.selected_index + 1) % len(self.layouts)
        self._update_highlight()
    
    def key_enter(self):
        selected_layout = self.layouts[self.selected_index]["name"]
        self.dismiss(selected_layout)
