import attr


@attr.s
class Session:
    """The session of pytask."""

    config = attr.ib(type=dict)
    """dict: A dictionary containing the configuration of the session."""
    hook = attr.ib()
    """pluggy.hooks._HookRelay: Holds all hooks collected by pytask."""
    collection_reports = attr.ib(default=None)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """
    tasks = attr.ib(default=None)
    """Optional[List[pytask.nodes.MetaTask]]: List of collected tasks."""
    deselected = attr.ib(default=[])
    """Optional[List[pytask.nodes.MetaTask]]: list of deselected tasks."""
    resolving_dependencies_report = attr.ib(default=None)
    """Optional[pytask.report.ResolvingDependenciesReport]: A report.

    Report when resolving dependencies failed.

    """
    execution_reports = attr.ib(default=None)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for executed tasks."""

    @classmethod
    def from_config(cls, config):
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
