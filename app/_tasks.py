from __future__ import annotations

from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from textual.widget import Widget


class TaskListRenderable:
    def __init__(self, tasks) -> None:
        self.tasks = tasks

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table.grid(expand=True)
        table.add_column()
        table.add_column(justify="right", max_width=8)

        for index, task_name in enumerate(self.tasks):

            table.add_row(
                index,
                task_name,
            )
        yield table


class Tasks(Widget):
    def __init__(self, tasks):
        self.tasks = tasks

    def render(self):
        return TaskListRenderable(self.tasks)
