"""Contains the main namespace for pytask."""
from __future__ import annotations

from _pytask import __version__
from _pytask.build import build
from _pytask.click import ColoredCommand
from _pytask.click import ColoredGroup
from _pytask.click import EnumChoice
from _pytask.collect_utils import depends_on
from _pytask.collect_utils import parse_nodes
from _pytask.collect_utils import produces
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.database_utils import BaseTable
from _pytask.database_utils import create_database
from _pytask.database_utils import DatabaseSession
from _pytask.database_utils import State
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
from _pytask.models import NodeInfo
from _pytask.node_protocols import MetaNode
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import PathNode
from _pytask.nodes import PythonNode
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
from _pytask.profile import Runtime
from _pytask.report import CollectionReport
from _pytask.report import DagReport
from _pytask.report import ExecutionReport
from _pytask.session import Session
from _pytask.task_utils import task
from _pytask.traceback import format_exception_without_traceback
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from _pytask.traceback import remove_traceback_from_exc_info
from _pytask.traceback import render_exc_info
from _pytask.typing import Product
from _pytask.warnings_utils import parse_warning_filter
from _pytask.warnings_utils import warning_record_to_str
from _pytask.warnings_utils import WarningReport


# This import must come last, otherwise a circular import occurs.
from _pytask.cli import cli  # noreorder


__all__ = [
    "BaseTable",
    "CollectionError",
    "CollectionMetadata",
    "CollectionOutcome",
    "CollectionReport",
    "ColoredCommand",
    "ColoredGroup",
    "ConfigurationError",
    "DagReport",
    "DatabaseSession",
    "EnumChoice",
    "ExecutionError",
    "ExecutionReport",
    "Exit",
    "ExitCode",
    "PathNode",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MetaNode",
    "NodeInfo",
    "NodeNotCollectedError",
    "NodeNotFoundError",
    "PathNode",
    "Persisted",
    "PNode",
    "PPathNode",
    "Product",
    "PTask",
    "PTaskWithPath",
    "PytaskError",
    "PythonNode",
    "ResolvingDependenciesError",
    "Runtime",
    "Session",
    "Skipped",
    "SkippedAncestorFailed",
    "SkippedUnchanged",
    "State",
    "Task",
    "TaskOutcome",
    "WarningReport",
    "__version__",
    "build",
    "build_dag",
    "check_for_optional_program",
    "cli",
    "console",
    "count_outcomes",
    "create_database",
    "depends_on",
    "format_exception_without_traceback",
    "get_all_marks",
    "get_marks",
    "has_mark",
    "hookimpl",
    "import_optional_dependency",
    "mark",
    "parse_nodes",
    "parse_warning_filter",
    "produces",
    "remove_internal_traceback_frames_from_exc_info",
    "remove_marks",
    "remove_traceback_from_exc_info",
    "render_exc_info",
    "set_marks",
    "task",
    "warning_record_to_str",
]
