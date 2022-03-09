"""This module contains the main namespace for pytask."""
from __future__ import annotations

from _pytask import __version__
from _pytask.build import main
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.graph import build_dag
from _pytask.mark import Mark
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.mark import MarkDecorator
from _pytask.mark import MarkGenerator
from _pytask.mark_utils import get_marks_from_obj
from _pytask.mark_utils import get_specific_markers_from_task
from _pytask.mark_utils import has_marker
from _pytask.mark_utils import remove_markers_from_func
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaNode
from _pytask.nodes import Task
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import count_outcomes
from _pytask.outcomes import Exit
from _pytask.outcomes import ExitCode
from _pytask.outcomes import Persisted
from _pytask.outcomes import Skipped
from _pytask.outcomes import SkippedAncestorFailed
from _pytask.outcomes import SkippedUnchanged
from _pytask.outcomes import TaskOutcome
from _pytask.session import Session

# This import must come last, otherwise a circular import occurs.
from _pytask.cli import cli  # noreorder


__all__ = [
    "__version__",
    "build_dag",
    "check_for_optional_program",
    "cli",
    "console",
    "count_outcomes",
    "get_marks_from_obj",
    "get_specific_markers_from_task",
    "has_marker",
    "hookimpl",
    "import_optional_dependency",
    "main",
    "mark",
    "remove_markers_from_func",
    "CollectionOutcome",
    "Exit",
    "ExitCode",
    "FilePathNode",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MetaNode",
    "Task",
    "Persisted",
    "Task",
    "Session",
    "Skipped",
    "SkippedAncestorFailed",
    "SkippedUnchanged",
    "TaskOutcome",
]
