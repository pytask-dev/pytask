"""This module contains the main namespace for pytask."""
from __future__ import annotations

from _pytask import __version__
from _pytask.build import main
from _pytask.collect_utils import depends_on
from _pytask.collect_utils import parse_nodes
from _pytask.collect_utils import produces
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.database import db
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeNotCollectedError
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import PytaskError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.graph import build_dag
from _pytask.mark import Mark
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.mark import MarkDecorator
from _pytask.mark import MarkGenerator
from _pytask.mark_utils import get_all_marks
from _pytask.mark_utils import get_marks
from _pytask.mark_utils import has_mark
from _pytask.mark_utils import remove_marks
from _pytask.mark_utils import set_marks
from _pytask.models import CollectionMetadata
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
from _pytask.report import CollectionReport
from _pytask.report import ExecutionReport
from _pytask.report import ResolvingDependenciesReport
from _pytask.session import Session
from _pytask.traceback import format_exception_without_traceback
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from _pytask.traceback import remove_traceback_from_exc_info
from _pytask.traceback import render_exc_info


# This import must come last, otherwise a circular import occurs.
from _pytask.cli import cli  # noreorder


__all__ = [
    "__version__",
    "build_dag",
    "check_for_optional_program",
    "cli",
    "console",
    "count_outcomes",
    "db",
    "depends_on",
    "format_exception_without_traceback",
    "get_all_marks",
    "get_first_non_none_value",
    "get_marks",
    "has_mark",
    "hookimpl",
    "import_optional_dependency",
    "main",
    "mark",
    "parse_nodes",
    "produces",
    "remove_internal_traceback_frames_from_exc_info",
    "remove_marks",
    "remove_traceback_from_exc_info",
    "render_exc_info",
    "set_marks",
    "CollectionError",
    "CollectionMetadata",
    "CollectionOutcome",
    "CollectionReport",
    "ConfigurationError",
    "ExecutionReport",
    "ExecutionError",
    "Exit",
    "ExitCode",
    "FilePathNode",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MetaNode",
    "NodeNotCollectedError",
    "NodeNotFoundError",
    "Persisted",
    "PytaskError",
    "ResolvingDependenciesError",
    "ResolvingDependenciesReport",
    "Session",
    "Skipped",
    "SkippedAncestorFailed",
    "SkippedUnchanged",
    "Task",
    "TaskOutcome",
]
