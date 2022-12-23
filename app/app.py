from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.table import Table
from textual.app import App as _App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Footer
from textual.widgets import Header


class TaskListRenderable:
    def __init__(self, tasks) -> None:
        self.tasks = tasks

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table.grid(expand=True)
        table.add_column()
        table.add_column(max_width=8)

        for index, task in enumerate(self.tasks):

            table.add_row(
                str(index),
                task["id"],
            )
        yield table


class TaskList(Widget):

    BINDINGS = [
        Binding("l,right,enter", "choose_path", "In", key_display="l", show=False),
        Binding("h,left", "goto_parent", "Out", key_display="h", show=False),
        Binding("j,down", "next_file", "Next", key_display="j", show=False),
        Binding("k,up", "prev_file", "Prev", key_display="k", show=False),
    ]

    def __init__(self, data, name=None, id=None, classes=None):
        super().__init__(name=name, id=id, classes=classes)
        self.data = data

    def render(self):
        return TaskListRenderable(self.data)


class App(_App):

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("ctrl+q", "quit", "Quit", key_display="ctrl+q"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield TaskList(self.data)
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def on_mount(self):

        self.data = data


if __name__ == "__main__":
    data = yaml.safe_load(Path("data.yaml").read_text())
    app = App()
    app.data = data
    app.run()
