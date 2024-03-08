"""Contains code related to the session object."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import networkx as nx
from attrs import define
from attrs import field
from pluggy import HookRelay

from _pytask.outcomes import ExitCode

if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.reports import CollectionReport
    from _pytask.reports import DagReport
    from _pytask.reports import ExecutionReport
    from _pytask.warnings_utils import WarningReport


@define(kw_only=True)
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

    config: dict[str, Any] = field(factory=dict)
    collection_reports: list[CollectionReport] = field(factory=list)
    dag: nx.DiGraph = field(factory=nx.DiGraph)
    hook: HookRelay = field(factory=HookRelay)
    tasks: list[PTask] = field(factory=list)
    dag_report: DagReport | None = None
    execution_reports: list[ExecutionReport] = field(factory=list)
    exit_code: ExitCode = ExitCode.OK

    collection_start: float = float("inf")
    collection_end: float = float("inf")
    execution_start: float = float("inf")
    execution_end: float = float("inf")

    n_tasks_failed: int = 0
    scheduler: Any = None
    should_stop: bool = False
    warnings: list[WarningReport] = field(factory=list)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Session:
        """Construct the class from a config."""
        hook = config["pm"].hook if "pm" in config else HookRelay()
        return cls(config=config, hook=hook)
