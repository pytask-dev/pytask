import math
import re
from pathlib import Path

import attr
import click


@attr.s
class CollectionReportTask:
    path = attr.ib(type=Path)
    name = attr.ib(type=str)
    task = attr.ib(default=None)
    exc_info = attr.ib(default=None)

    @classmethod
    def from_task(cls, task):
        return cls(path=task.path, name=task.name, task=task)

    @classmethod
    def from_exception(cls, path, name, exc_info):
        return cls(path=path, name=name, exc_info=exc_info)

    @property
    def successful(self):
        return self.exc_info is None

    def format_title(self):
        return f" Collection of task '{self.name}' in '{self.path}' failed "


@attr.s
class CollectionReportFile:
    path = attr.ib(type=Path)
    exc_info = attr.ib(default=None)

    @classmethod
    def from_exception(cls, path, exc_info):
        return cls(path, exc_info=exc_info)

    @property
    def successful(self):
        return self.exc_info is None

    def format_title(self):
        return f" Collection of file '{self.path}' failed "


@attr.s
class ResolvingDependenciesReport:
    exc_info = attr.ib()


@attr.s
class ExecutionReport:
    task = attr.ib()
    success = attr.ib(type=bool)
    exc_info = attr.ib(default=None)

    @classmethod
    def from_task_and_exception(cls, task, exc_info):
        return cls(task, False, exc_info)

    @classmethod
    def from_task(cls, task):
        return cls(task, True)


def format_execute_footer(n_successful, n_failed, duration, terminal_width):
    message = []
    if n_successful:
        message.append(click.style(f"{n_successful} succeeded", fg="green"))
    if n_failed:
        message.append(click.style(f"{n_failed} failed", fg="red"))
    message = " " + ", ".join(message) + " "

    color = "red" if n_failed else "green"
    message += click.style(f"in {duration} second(s) ", fg=color)

    formatted_message = _wrap_string_ignoring_ansi_colors(
        message, color, terminal_width
    )

    return formatted_message


def _wrap_string_ignoring_ansi_colors(message, color, width):
    n_characters = width - len(_remove_ansi_colors(message))
    n_left, n_right = math.floor(n_characters / 2), math.ceil(n_characters / 2)

    return (
        click.style("=" * n_left, fg=color)
        + message
        + click.style("=" * n_right, fg=color)
    )


def _remove_ansi_colors(string):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)
