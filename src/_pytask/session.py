"""Contains code related to the session object."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any

import networkx as nx
from pluggy import HookRelay

from _pytask.outcomes import ExitCode

if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.reports import CollectionReport
    from _pytask.reports import DagReport
    from _pytask.reports import ExecutionReport
    from _pytask.warnings_utils import WarningReport


@dataclass(kw_only=True)
class Session:
    """The session of pytask.

    Parameters
    ----------
    config
        Configuration of the session.
    collection_reports
        Reports for collected items.
    dag
        The DAG of the project.
    hook
        Holds all hooks collected by pytask.
    tasks
        List of collected tasks.
    dag_reports
        Reports for resolving dependencies failed.
    execution_reports
        Reports for executed tasks.
    n_tasks_failed
        Number of tests which have failed.
    should_stop
        Indicates whether the session should be stopped.
    warnings
        A list of warnings captured during the run.

    """

    config: dict[str, Any] = field(default_factory=dict)
    collection_reports: list[CollectionReport] = field(default_factory=list)
    dag: nx.DiGraph = field(default_factory=nx.DiGraph)
    hook: HookRelay = field(default_factory=HookRelay)
    tasks: list[PTask] = field(default_factory=list)
    dag_report: DagReport | None = None
    execution_reports: list[ExecutionReport] = field(default_factory=list)
    exit_code: ExitCode = ExitCode.OK

    collection_start: float = float("inf")
    collection_end: float = float("inf")
    execution_start: float = float("inf")
    execution_end: float = float("inf")

    n_tasks_failed: int = 0
    scheduler: Any = None
    should_stop: bool = False
    warnings: list[WarningReport] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Session:
        """Construct the class from a config."""
        hook = config["pm"].hook if "pm" in config else HookRelay()
        return cls(config=config, hook=hook)
