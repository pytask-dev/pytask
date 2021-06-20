from typing import Any
from typing import Dict

import attr
from _pytask.shared import reduce_node_name
from rich.align import Align
from rich.live import Live
from rich.status import Status
from rich.table import Table
from rich.text import Text


def generate_collection_status(n_collected_tasks):
    """Generate the status object to display the progress during collection."""
    return Status(
        f"Collected {n_collected_tasks} tasks.", refresh_per_second=4, spinner="dots"
    )


def generate_execution_table(reports, paths):
    table = Table("Task", "Outcome")
    for report in reports:
        reduced_task_name = reduce_node_name(report.task, paths)
        table.add_row(reduced_task_name, Text(report.symbol, style=report.color))

    return Align.center(table)


@attr.s
class LiveWrapper:
    """Wrap :class:`rich.live.Live` for conditional verbosity."""

    verbose = attr.ib(type=int)
    live = attr.ib()

    @classmethod
    def from_verbose_and_live_kwargs(cls, verbose: int, **live_kwargs: Dict[str, Any]):
        live = Live(**live_kwargs)
        return cls(verbose, live)

    def __enter__(self):
        if self.verbose >= 1:
            return self.live.__enter__()
        else:
            return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.verbose >= 1:
            return self.live.__exit__(exc_type, exc_value, exc_tb)
        else:
            return None

    @staticmethod
    def update(*args, **kwargs):  # noqa: U100
        return None

    @staticmethod
    def refresh():
        return None
