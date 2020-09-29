import attr
from _pytask.enums import ExitCode


@attr.s
class Session:
    """The session of pytask."""

    config = attr.ib(factory=dict)
    """dict: A dictionary containing the configuration of the session."""
    hook = attr.ib(default=None)
    """pluggy.hooks._HookRelay: Holds all hooks collected by pytask."""
    collection_reports = attr.ib(factory=list)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks = attr.ib(factory=list)
    """Optional[List[pytask.nodes.MetaTask]]: List of collected tasks."""
    deselected = attr.ib(factory=list)
    """Optional[List[pytask.nodes.MetaTask]]: list of deselected tasks."""
    resolving_dependencies_report = attr.ib(factory=list)
    """Optional[pytask.report.ResolvingDependenciesReport]: A report.

    Report when resolving dependencies failed.

    """
    execution_reports = attr.ib(factory=list)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for executed tasks."""
    exit_code = attr.ib(default=ExitCode.OK)

    @classmethod
    def from_config(cls, config):
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
