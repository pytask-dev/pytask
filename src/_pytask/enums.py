import enum


class ExitCode(enum.IntEnum):
    """Exit codes for pytask."""

    OK = 0
    """Tasks were executed successfully."""

    FAILED = 1
    """Failed while executing tasks."""

    COLLECTION_FAILED = 2
    """Failed while collecting tasks."""

    RESOLVING_DEPENDENCIES_FAILED = 3
    """Failed while resolving dependencies."""


class ColorCode(enum.Enum):
    """Color codes for pytask."""

    SUCCESS = "green"

    FAILED = "red"

    SKIPPED = "yellow"
