"""Contains code related to outcomes."""
from __future__ import annotations

from enum import auto
from enum import Enum
from enum import IntEnum
from typing import Sequence
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytask.report import CollectionReport
    from _pytask.report import ExecutionReport


__all__ = [
    "CollectionOutcome",
    "Exit",
    "ExitCode",
    "Persisted",
    "PytaskOutcome",
    "Skipped",
    "SkippedAncestorFailed",
    "SkippedUnchanged",
    "TaskOutcome",
    "count_outcomes",
]


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
    def description(self) -> str:
        """A description of an outcome used in the summary panel."""
        descriptions = {
            CollectionOutcome.SUCCESS: "Succeeded",
            CollectionOutcome.FAIL: "Failed",
        }
        assert len(descriptions) == len(CollectionOutcome)
        return descriptions[self]

    @property
    def style(self) -> str:
        """Return the style of an outcome."""
        styles = {
            CollectionOutcome.SUCCESS: "success",
            CollectionOutcome.FAIL: "failed",
        }
        assert len(styles) == len(CollectionOutcome)
        return styles[self]

    @property
    def style_textonly(self) -> str:
        """Return the style of an outcome when only the text is colored."""
        styles_textonly = {
            CollectionOutcome.SUCCESS: "success.textonly",
            CollectionOutcome.FAIL: "failed.textonly",
        }
        assert len(styles_textonly) == len(CollectionOutcome)
        return styles_textonly[self]


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
    WOULD_BE_EXECUTED = auto()

    @property
    def symbol(self) -> str:
        """The symbol of an outcome."""
        symbols = {
            TaskOutcome.SUCCESS: ".",
            TaskOutcome.PERSISTENCE: "p",
            TaskOutcome.SKIP_UNCHANGED: "s",
            TaskOutcome.SKIP: "s",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "F",
            TaskOutcome.FAIL: "F",
            TaskOutcome.WOULD_BE_EXECUTED: "w",
        }
        assert len(symbols) == len(TaskOutcome)
        return symbols[self]

    @property
    def description(self) -> str:
        """A description of an outcome used in the summary panel."""
        descriptions = {
            TaskOutcome.SUCCESS: "Succeeded",
            TaskOutcome.PERSISTENCE: "Persisted",
            TaskOutcome.SKIP_UNCHANGED: "Skipped because unchanged",
            TaskOutcome.SKIP: "Skipped",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "Skipped because previous failed",
            TaskOutcome.FAIL: "Failed",
            TaskOutcome.WOULD_BE_EXECUTED: "Would be executed",
        }
        assert len(descriptions) == len(TaskOutcome)
        return descriptions[self]

    @property
    def style(self) -> str:
        """Return the style of an outcome."""
        styles = {
            TaskOutcome.SUCCESS: "success",
            TaskOutcome.PERSISTENCE: "success",
            TaskOutcome.SKIP_UNCHANGED: "success",
            TaskOutcome.SKIP: "skipped",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "failed",
            TaskOutcome.FAIL: "failed",
            TaskOutcome.WOULD_BE_EXECUTED: "success",
        }
        assert len(styles) == len(TaskOutcome)
        return styles[self]

    @property
    def style_textonly(self) -> str:
        """Return the style of an outcome when only the text is colored."""
        styles_textonly = {
            TaskOutcome.SUCCESS: "success.textonly",
            TaskOutcome.PERSISTENCE: "success.textonly",
            TaskOutcome.SKIP_UNCHANGED: "success.textonly",
            TaskOutcome.SKIP: "skipped.textonly",
            TaskOutcome.SKIP_PREVIOUS_FAILED: "failed.textonly",
            TaskOutcome.FAIL: "failed.textonly",
            TaskOutcome.WOULD_BE_EXECUTED: "success.textonly",
        }
        assert len(styles_textonly) == len(TaskOutcome)
        return styles_textonly[self]


def count_outcomes(
    reports: Sequence[CollectionReport | ExecutionReport],
    outcome_enum: type[CollectionOutcome | TaskOutcome],
) -> dict[Enum, int]:
    """Count how often an outcome occurred.

    Examples
    --------
    >>> from _pytask.outcomes import CollectionOutcome, TaskOutcome
    >>> count_outcomes([], CollectionOutcome)
    {<CollectionOutcome.SUCCESS: 1>: 0, <CollectionOutcome.FAIL: 2>: 0}

    """
    return {
        outcome: len([r for r in reports if r.outcome == outcome])
        for outcome in outcome_enum
    }


class ExitCode(IntEnum):
    """Exit codes for pytask."""

    OK = 0
    """Tasks were executed successfully."""

    FAILED = 1
    """Failed while executing tasks."""

    CONFIGURATION_FAILED = 2

    COLLECTION_FAILED = 3
    """Failed while collecting tasks."""

    DAG_FAILED = 4
    """Failed while building the DAG."""


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


class WouldBeExecuted(PytaskOutcome):
    """Outcome if a task would be executed."""


class Exit(Exception):
    """Raised for immediate program exits (no tracebacks/summaries)."""

    def __init__(
        self, msg: str = "unknown reason", returncode: int | None = None
    ) -> None:
        self.msg = msg
        self.returncode = returncode
        super().__init__(msg)
