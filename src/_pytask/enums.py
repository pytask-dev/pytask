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
