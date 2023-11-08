"""Contains the main namespace for pytask."""
from __future__ import annotations

from _pytask import __version__
from _pytask._hashlib import hash_value
from _pytask.build import build
from _pytask.click import ColoredCommand
from _pytask.click import ColoredGroup
from _pytask.click import EnumChoice
from _pytask.collect_utils import depends_on
from _pytask.collect_utils import parse_dependencies_from_task_function
from _pytask.collect_utils import parse_products_from_task_function
from _pytask.collect_utils import produces
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.dag_command import build_dag
from _pytask.data_catalog import DataCatalog
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
from _pytask.nodes import PickleNode
from _pytask.nodes import PythonNode
from _pytask.nodes import Task
from _pytask.nodes import TaskWithoutPath
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
from _pytask.reports import CollectionReport
from _pytask.reports import DagReport
from _pytask.reports import ExecutionReport
from _pytask.session import Session
from _pytask.task_utils import task
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from _pytask.traceback import Traceback
from _pytask.typing import is_task_function
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
    "DataCatalog",
    "DatabaseSession",
    "EnumChoice",
    "ExecutionError",
    "ExecutionReport",
    "Exit",
    "ExitCode",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MetaNode",
    "NodeInfo",
    "NodeNotCollectedError",
    "NodeNotFoundError",
    "PNode",
    "PPathNode",
    "PTask",
    "PTaskWithPath",
    "PathNode",
    "Persisted",
    "PickleNode",
    "Product",
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
    "TaskWithoutPath",
    "Traceback",
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
    "get_all_marks",
    "get_marks",
    "has_mark",
    "hash_value",
    "hookimpl",
    "import_optional_dependency",
    "is_task_function",
    "mark",
    "parse_dependencies_from_task_function",
    "parse_products_from_task_function",
    "parse_warning_filter",
    "produces",
    "remove_internal_traceback_frames_from_exc_info",
    "remove_marks",
    "set_marks",
    "task",
    "warning_record_to_str",
]
