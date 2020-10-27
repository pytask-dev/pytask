"""This module contains everything related to reports."""
import math
import re
from pathlib import Path

import attr
import click
from _pytask.enums import ColorCode
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info


@attr.s
class CollectionReport:
    """A general collection report."""

    title = attr.ib(type=str)
    exc_info = attr.ib(type=tuple)

    def format_title(self):
        return self.title

    @property
    def successful(self):
        return self.exc_info is None


@attr.s
class CollectionReportTask:
    """A collection report for a task."""

    path = attr.ib(type=Path)
    name = attr.ib(type=str)
    task = attr.ib(default=None)
    exc_info = attr.ib(default=None)

    @classmethod
    def from_task(cls, task):
        return cls(path=task.path, name=task.name, task=task)

    @classmethod
    def from_exception(cls, path, name, exc_info):
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(path=path, name=name, exc_info=exc_info)

    @property
    def successful(self):
        return self.exc_info is None

    def format_title(self):
        return f" Collection of task '{self.name}' in '{self.path}' failed "


@attr.s
class CollectionReportFile:
    """A collection report for a file."""

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
    """A report for an error while resolving dependencies."""

    exc_info = attr.ib()

    @classmethod
    def from_exception(cls, exc_info):
        return cls(exc_info)


@attr.s
class ExecutionReport:
    """A report for an executed task."""

    task = attr.ib()
    success = attr.ib(type=bool)
    exc_info = attr.ib(default=None)
    sections = attr.ib(factory=list)

    @classmethod
    def from_task_and_exception(cls, task, exc_info):
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(task, False, exc_info, task._report_sections)

    @classmethod
    def from_task(cls, task):
        return cls(task, True, None, task._report_sections)


def format_execute_footer(n_successful, n_failed, duration, terminal_width):
    """Format the footer of the execution."""
    message = []
    if n_successful:
        message.append(
            click.style(f"{n_successful} succeeded", fg=ColorCode.SUCCESS.value)
        )
    if n_failed:
        message.append(click.style(f"{n_failed} failed", fg=ColorCode.FAILED.value))
    message = " " + ", ".join(message) + " "

    color = ColorCode.FAILED.value if n_failed else ColorCode.SUCCESS.value
    message += click.style(f"in {duration}s ", fg=color)

    formatted_message = _wrap_string_ignoring_ansi_colors(
        message, color, terminal_width
    )

    return formatted_message


def format_collect_footer(
    n_successful, n_failed, n_deselected, duration, terminal_width
):
    """Format the footer of the execution."""
    message = []
    if n_successful:
        message.append(
            click.style(f"{n_successful} collected", fg=ColorCode.SUCCESS.value)
        )
    if n_failed:
        message.append(click.style(f"{n_failed} failed", fg=ColorCode.FAILED.value))
    if n_deselected:
        message.append(click.style(f"{n_deselected} deselected", fg="white"))
    message = " " + ", ".join(message) + " "

    color = ColorCode.FAILED.value if n_failed else ColorCode.SUCCESS.value
    message += click.style(f"in {duration}s ", fg=color)

    formatted_message = _wrap_string_ignoring_ansi_colors(
        message, color, terminal_width
    )

    return formatted_message


def _wrap_string_ignoring_ansi_colors(message, color, width):
    """Wrap a string with ANSI colors.

    This wrapper ignores the color codes which will increase the length of the string,
    but will not show up in the printed string.

    """
    n_characters = width - len(_remove_ansi_colors(message))
    n_left, n_right = math.floor(n_characters / 2), math.ceil(n_characters / 2)

    return (
        click.style("=" * n_left, fg=color)
        + message
        + click.style("=" * n_right, fg=color)
    )


def _remove_ansi_colors(string):
    """Remove ANSI colors from a string."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)
