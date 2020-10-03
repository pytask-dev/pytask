class PytaskOutcome(Exception):
    """Base outcome of a task."""


class Skipped(PytaskOutcome):
    """Outcome if task is skipped."""


class SkippedAncestorFailed(PytaskOutcome):
    """Outcome if an ancestor failed."""


class SkippedDependencyNotFound(PytaskOutcome):
    """Outcome if a dependency was not found."""


class SkippedUnchanged(PytaskOutcome):
    """Outcome if task has run before and is unchanged."""


class Persisted(PytaskOutcome):
    """Outcome if task should persist."""
