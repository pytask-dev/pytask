from typing import Optional


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
