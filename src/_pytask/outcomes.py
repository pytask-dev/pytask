"""This module contains code related to outcomes."""
from enum import auto
from enum import Enum
from typing import Optional


class TaskOutcome(Enum):
    """Outcomes of tasks.

    Attributes
    ----------
    FAIL
        Outcome for failed tasks.
    PERSISTENCE
        Outcome for tasks which should persist. Even if dependencies or products have
        changed, skip the task, update all hashes to the new ones, mark it as
        successful.
    SKIP
        Outcome for skipped tasks.
    SKIP_PREVIOUS_FAILED
        Outcome for tasks where a necessary preceding task has failed and, thus, this
        task could not have been executed.
    SKIP_UNCHANGED
        Outcome for tasks which do not need to be executed since all dependencies,
        source files and products have not changed.
    SUCCESS
        Outcome for task which was executed successfully.

    """

    SUCCESS = auto()
    PERSISTENCE = auto()
    SKIP_UNCHANGED = auto()
    SKIP = auto()
    SKIP_PREVIOUS_FAILED = auto()
    FAIL = auto()

    @property
    def display_char(self) -> str:
        display_chars = {
            TaskOutcome.SUCCESS: ".",
            TaskOutcome.PERSISTENCE: "p",
            TaskOutcome.SKIP_UNCHANGED: "s",
            TaskOutcome.SKIP: "s",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "F",
            TaskOutcome.FAIL: "F",
        }
        assert len(display_chars) == len(TaskOutcome)
        return display_chars[self]

    @property
    def display_name(self) -> str:
        display_names = {
            TaskOutcome.SUCCESS: "Succeeded",
            TaskOutcome.PERSISTENCE: "Persisted",
            TaskOutcome.SKIP_UNCHANGED: "Skipped because unchanged",
            TaskOutcome.SKIP: "Skipped",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "Skipped because previous failed",
            TaskOutcome.FAIL: "Failed",
        }
        assert len(display_names) == len(TaskOutcome)
        return display_names[self]


class PytaskOutcome(Exception):
    """Base outcome of a task."""


class Skipped(PytaskOutcome):
    """Outcome if task is skipped."""


class SkippedAncestorFailed(PytaskOutcome):
    """Outcome if an ancestor failed."""


class SkippedUnchanged(PytaskOutcome):
    """Outcome if task has run before and is unchanged."""


class Persisted(PytaskOutcome):
    """Outcome if task should persist."""


class Exit(Exception):
    """Raised for immediate program exits (no tracebacks/summaries)."""

    def __init__(
        self, msg: str = "unknown reason", returncode: Optional[int] = None
    ) -> None:
        self.msg = msg
        self.returncode = returncode
        super().__init__(msg)
