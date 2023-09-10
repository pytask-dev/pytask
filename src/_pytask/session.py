"""Contains code related to the session object."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.outcomes import ExitCode
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.warnings_utils import WarningReport
    from pluggy._hooks import _HookRelay
    import networkx as nx
    from _pytask.report import CollectionReport
    from _pytask.report import ExecutionReport
    from _pytask.report import DagReport


@define
class Session:
    """The session of pytask."""

    config: dict[str, Any] = field(factory=dict)
    """Configuration of the session."""
    hook: _HookRelay | None = None
    """Holds all hooks collected by pytask."""
    collection_reports: list[CollectionReport] = field(factory=list)
    """Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks: list[PTask] = field(factory=list)
    """List of collected tasks."""
    dag: nx.DiGraph | None = None
    resolving_dependencies_report: DagReport | None = None
    """Reports for resolving dependencies failed."""
    execution_reports: list[ExecutionReport] = field(factory=list)
    """Reports for executed tasks."""
    exit_code: ExitCode = ExitCode.OK

    collection_start: float | None = None
    collection_end: float | None = None
    execution_start: float | None = None
    execution_end: float | None = None

    n_tasks_failed: int = 0
    """Number of tests which have failed."""
    scheduler: Any = None
    should_stop: bool = False
    """Indicates whether the session should be stopped."""
    warnings: list[WarningReport] = field(factory=list)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Session:
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
