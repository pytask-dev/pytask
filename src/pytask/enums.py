import enum


class ExitCode(enum.IntEnum):
    """Exit codes for pytask."""

    # Tasks were executed successfully.
    OK = 0

    # An error occurred while executing tasks.
    FAILED = 1
