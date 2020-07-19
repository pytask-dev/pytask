class PytaskError(Exception):
    """Base exception for pytask which should be inherited by all other exceptions."""


class NodeNotFoundError(PytaskError):
    """Exception for missing dependencies."""


class NodeNotCollectedError(PytaskError):
    """Exception for nodes which could not be collected."""


class CollectionError(PytaskError):
    """Exception during collection."""


class ResolvingDependenciesError(PytaskError):
    """Exception during resolving dependencies."""


class ExecutionError(PytaskError):
    """Exception during execution."""


class TaskDuplicatedError(PytaskError):
    """Exception for duplicated task during collection."""
