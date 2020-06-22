import enum


class ExitCode(enum.IntEnum):
    """Exit codes for pytask."""

    # Tasks were executed successfully.
    OK = 0

    # Failed while executing tasks.
    FAILED = 1

    # Failed while collecting tasks.
    COLLECTION_FAILED = 2

    # Failed while resolving dependencies.
    RESOLVING_DEPENDENCIES_FAILED = 3
