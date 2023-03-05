"""This module contains code related to the session object."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

import networkx as nx
from _pytask.outcomes import ExitCode
from _pytask.warnings_utils import WarningReport
from attrs import define
from attrs import field

# Location was moved from pluggy v0.13.1 to v1.0.0.
try:
    from pluggy._hooks import _HookRelay
except ImportError:
    from pluggy.hooks import _HookRelay


if TYPE_CHECKING:
    from _pytask.report import CollectionReport
    from _pytask.report import ExecutionReport
    from _ptytask.report import DagReport
    from _pytask.nodes_utils import Task


@define
class Session:
    """The session of pytask."""

    config: dict[str, Any] = field(factory=dict)
    """Dict[str, Any]: Configuration of the session."""
    hook: _HookRelay | None = None
    """pluggy.hooks._HookRelay | None: Holds all hooks collected by pytask."""
    collection_reports: list[CollectionReport] = field(factory=list)
    """list[CollectionReport]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks: list[Task] = field(factory=list)
    """list[Task]: List of collected tasks."""
    dag: nx.DiGraph | None = None
    resolving_dependencies_report: DagReport | None = None
    """DagReport | None: Reports for resolving dependencies failed."""
    execution_reports: list[ExecutionReport] = field(factory=list)
    """list[ExecutionReport]: Reports for executed tasks."""
    exit_code: ExitCode = ExitCode.OK

    collection_start: float | None = None
    collection_end: float | None = None
    execution_start: float | None = None
    execution_end: float | None = None

    n_tasks_failed: int = 0
    """int | None: Number of tests which have failed."""
    scheduler: Any = None
    should_stop: bool = False
    """bool | None: Indicates whether the session should be stopped."""
    warnings: list[WarningReport] = field(factory=list)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Session:
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
