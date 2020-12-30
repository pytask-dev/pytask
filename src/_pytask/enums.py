"""Enumerations for pytask."""
import enum


class ExitCode(enum.IntEnum):
    """Exit codes for pytask."""

    OK = 0
    """Tasks were executed successfully."""

    FAILED = 1
    """Failed while executing tasks."""

    CONFIGURATION_FAILED = 2

    COLLECTION_FAILED = 3
    """Failed while collecting tasks."""

    RESOLVING_DEPENDENCIES_FAILED = 4
    """Failed while resolving dependencies."""


class ColorCode(str, enum.Enum):
    """Color codes for pytask."""

    SUCCESS = "green"

    FAILED = "red"

    SKIPPED = "yellow"

    NEUTRAL = None

    def __str__(self) -> str:
        """Allows to use a color code inside f-strings without the need for .value."""
        return str.__str__(self)
