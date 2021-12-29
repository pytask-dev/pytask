"""This module contains code related to outcomes."""
from enum import auto
from enum import Enum
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:
    from _pytask.report import CollectionReport
    from _pytask.report import ExecutionReport


class CollectionOutcome(Enum):
    """Outcomes of collected files or tasks.

    Attributes
    ----------
    FAIL
        Outcome for failed collected files or tasks.
    SUCCESS
        Outcome for task which was executed successfully.

    """

    SUCCESS = auto()
    FAIL = auto()

    @property
    def symbol(self) -> str:
        symbols = {
            CollectionOutcome.SUCCESS: ".",
            CollectionOutcome.FAIL: "F",
        }
        assert len(symbols) == len(CollectionOutcome)
        return symbols[self]

    @property
    def description(self) -> str:
        descriptions = {
            CollectionOutcome.SUCCESS: "succeeded",
            CollectionOutcome.FAIL: "failed",
        }
        assert len(descriptions) == len(CollectionOutcome)
        return descriptions[self]

    @property
    def style(self) -> str:
        styles = {
            CollectionOutcome.SUCCESS: "success",
            CollectionOutcome.FAIL: "failed",
        }
        assert len(styles) == len(CollectionOutcome)
        return styles[self]


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
    def symbol(self) -> str:
        symbols = {
            TaskOutcome.SUCCESS: ".",
            TaskOutcome.PERSISTENCE: "p",
            TaskOutcome.SKIP_UNCHANGED: "s",
            TaskOutcome.SKIP: "s",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "F",
            TaskOutcome.FAIL: "F",
        }
        assert len(symbols) == len(TaskOutcome)
        return symbols[self]

    @property
    def description(self) -> str:
        descriptions = {
            TaskOutcome.SUCCESS: "succeeded",
            TaskOutcome.PERSISTENCE: "persisted",
            TaskOutcome.SKIP_UNCHANGED: "skipped because unchanged",
            TaskOutcome.SKIP: "skipped",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "skipped because previous failed",
            TaskOutcome.FAIL: "failed",
        }
        assert len(descriptions) == len(TaskOutcome)
        return descriptions[self]

    @property
    def style(self) -> str:
        styles = {
            TaskOutcome.SUCCESS: "success",
            TaskOutcome.PERSISTENCE: "success",
            TaskOutcome.SKIP_UNCHANGED: "success",
            TaskOutcome.SKIP: "skipped",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "failed",
            TaskOutcome.FAIL: "failed",
        }
        assert len(styles) == len(TaskOutcome)
        return styles[self]


def count_outcomes(
    reports: Sequence[Union["CollectionReport", "ExecutionReport"]],
    outcome_enum: Type[Enum],
) -> Dict[Enum, int]:
    """Count how often an outcome occurred."""
    return {
        outcome: len([r for r in reports if r.outcome == outcome])
        for outcome in outcome_enum
    }


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
