"""This module contains everything related to reports."""
import attr
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info


@attr.s
class CollectionReport:
    """A collection report for a task."""

    node = attr.ib(default=None)
    exc_info = attr.ib(default=None)

    @classmethod
    def from_node(cls, node):
        return cls(node=node)

    @classmethod
    def from_exception(cls, exc_info, node=None):
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(exc_info=exc_info, node=node)

    @property
    def successful(self):
        return self.exc_info is None


@attr.s
class ResolvingDependenciesReport:
    """A report for an error while resolving dependencies."""

    exc_info = attr.ib()

    @classmethod
    def from_exception(cls, exc_info):
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(exc_info)


@attr.s
class ExecutionReport:
    """A report for an executed task."""

    task = attr.ib()
    success = attr.ib(type=bool)
    exc_info = attr.ib(default=None)
    sections = attr.ib(factory=list)

    @classmethod
    def from_task_and_exception(cls, task, exc_info):
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(task, False, exc_info, task._report_sections)

    @classmethod
    def from_task(cls, task):
        return cls(task, True, None, task._report_sections)
