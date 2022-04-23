"""This module contains code related to the session object."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List  # noqa: F401
from typing import Optional
from typing import TYPE_CHECKING

import attr
import networkx as nx
from _pytask.outcomes import ExitCode
from _pytask.warnings_utils import WarningReport

# Location was moved from pluggy v0.13.1 to v1.0.0.
try:
    from pluggy._hooks import _HookRelay
except ImportError:
    from pluggy.hooks import _HookRelay


if TYPE_CHECKING:
    from _pytask.report import CollectionReport
    from _pytask.report import ExecutionReport
    from _ptytask.report import ResolvingDependenciesReport
    from _pytask.nodes import Task


@attr.s
class Session:
    """The session of pytask."""

    config = attr.ib(factory=dict, type=Dict[str, Any])
    """Dict[str, Any]: Configuration of the session."""
    hook = attr.ib(default=None, type=Optional[_HookRelay])
    """Optional[pluggy.hooks._HookRelay]: Holds all hooks collected by pytask."""
    collection_reports = attr.ib(factory=list, type=List["CollectionReport"])
    """List[CollectionReport]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks = attr.ib(factory=list, type=List["Task"])
    """List[Task]: List of collected tasks."""
    dag = attr.ib(default=None, type=Optional[nx.DiGraph])
    resolving_dependencies_report = attr.ib(
        default=None, type=Optional["ResolvingDependenciesReport"]
    )
    """Optional[ResolvingDependenciesReport]: Reports for resolving dependencies
    failed."""
    execution_reports = attr.ib(factory=list, type=List["ExecutionReport"])
    """List[ExecutionReport]: Reports for executed tasks."""
    exit_code = attr.ib(default=ExitCode.OK, type=ExitCode)

    collection_start = attr.ib(default=None, type=Optional[float])
    collection_end = attr.ib(default=None, type=Optional[float])
    execution_start = attr.ib(default=None, type=Optional[float])
    execution_end = attr.ib(default=None, type=Optional[float])

    n_tasks_failed = attr.ib(default=0, type=Optional[int])
    """Optional[int]: Number of tests which have failed."""
    scheduler = attr.ib(default=None, type=Any)
    should_stop = attr.ib(default=False, type=Optional[bool])
    """Optional[bool]: Indicates whether the session should be stopped."""
    warnings = attr.ib(factory=list, type=List[WarningReport])

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Session:
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
