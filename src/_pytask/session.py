from typing import Any
from typing import Dict
from typing import List  # noqa: F401
from typing import Optional
from typing import TYPE_CHECKING

import attr
import pluggy
from _pytask.enums import ExitCode


if TYPE_CHECKING:
    from _pytask.report import ExecutionReport  # noqa: F401
    from _ptytask.report import ResolvingDependenciesReport  # noqa: F401
    from _pytask.nodes import MetaTask  # noqa: F401


@attr.s
class Session:
    """The session of pytask."""

    config = attr.ib(factory=dict, type=Optional[Dict[str, Any]])
    """Optional[Dict[str, Any]]: Configuration of the session."""
    hook = attr.ib(default=None, type=Optional[pluggy.hooks._HookRelay])
    """Optional[pluggy.hooks._HookRelay]: Holds all hooks collected by pytask."""
    collection_reports = attr.ib(factory=list, type="List[ExecutionReport]")
    """Optional[List[pytask.report.ExecutionReport]]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks = attr.ib(factory=list, type="Optional[List[MetaTask]]")
    """Optional[List[MetaTask]]: List of collected tasks."""
    resolving_dependencies_report = attr.ib(
        factory=list, type="Optional[List[ResolvingDependenciesReport]]"
    )
    """Optional[List[ResolvingDependenciesReport]]: Reports for resolving dependencies
    failed."""
    execution_reports = attr.ib(factory=list, type="Optional[List[ExecutionReport]]")
    """Optional[List[ExecutionReport]]: Reports for executed tasks."""
    exit_code = attr.ib(default=ExitCode.OK, type=ExitCode)

    collection_start = attr.ib(default=None, type=Optional[float])
    collection_end = attr.ib(default=None, type=Optional[float])
    execution_start = attr.ib(default=None, type=Optional[float])
    execution_end = attr.ib(default=None, type=Optional[float])

    n_tasks_failed = attr.ib(default=0, type=Optional[int])
    """Optional[int]: Number of tests which have failed."""
    should_stop = attr.ib(default=False, type=Optional[bool])
    """Optional[bool]: Indicates whether the session should be stopped."""

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Session":
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
