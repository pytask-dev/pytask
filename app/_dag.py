from __future__ import annotations


from kupo._directory import DirectoryListRenderable
from rich.text import Text
from textual.binding import Binding
from textual.widgets import Static


class Dag(Static, can_focus=True):
    COMPONENT_CLASSES = {
        "preview--body",
        "directory--meta-column",
        "directory--dir",
    }

    BINDINGS = [
        Binding("g", "top", "Home", key_display="g"),
        Binding("G", "bottom", "End", key_display="G"),
        Binding("j", "down", "Down", key_display="j"),
        Binding("k", "up", "Up", key_display="k"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self._content_height = None
        self._content_width = None

    def show_dag(self) -> None:
        self.update(Text("Here comes the dag."))

    def action_up(self):
        self.parent.scroll_up(animate=False)

    def action_down(self):
        # TODO: This condition is a hack to workaround Textual seemingly scrolling
        #  1 more than it should, even when no vertical scrollbar.
        if not isinstance(self.renderable, DirectoryListRenderable):
            self.parent.scroll_down(animate=False)

    def action_top(self):
        self.parent.scroll_home(animate=False)

    def action_bottom(self):
        self.parent.scroll_end(animate=False)
