"""Contains the main code for the markers plugin."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from typing import Any

import click
from attrs import define
from rich.table import Table

from _pytask.click import ColoredCommand
from _pytask.console import console
from _pytask.dag_utils import task_and_preceding_tasks
from _pytask.exceptions import ConfigurationError
from _pytask.mark.expression import Expression
from _pytask.mark.expression import ParseError
from _pytask.mark.structures import MARK_GEN
from _pytask.mark.structures import Mark
from _pytask.mark.structures import MarkDecorator
from _pytask.mark.structures import MarkGenerator
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.session import Session
from _pytask.shared import parse_markers

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet
    from typing import NoReturn

    import networkx as nx

    from _pytask.node_protocols import PTask


__all__ = [
    "MARK_GEN",
    "Expression",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "ParseError",
    "select_by_after_keyword",
    "select_by_keyword",
    "select_by_mark",
    "select_tasks_by_marks_and_expressions",
]


@click.command(cls=ColoredCommand)
def markers(**raw_config: Any) -> NoReturn:
    """Show all registered markers."""
    raw_config["command"] = "markers"
    pm = storage.get()

    try:
        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):  # pragma: no cover
        console.print_exception()
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)

    else:
        table = Table("Marker", "Description", leading=1)

        for name, description in config["markers"].items():
            table.add_row(f"pytask.mark.{name}", description)

        console.print(table)

    session.hook.pytask_unconfigure(session=session)
    sys.exit(session.exit_code)


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Add marker related options."""
    cli.add_command(markers)

    additional_build_parameters = [
        click.Option(
            ["--strict-markers"],
            is_flag=True,
            help="Raise errors for unknown markers.",
            default=False,
        ),
        click.Option(
            ["-m", "marker_expression"],
            metavar="MARKER_EXPRESSION",
            type=str,
            help="Select tasks via marker expressions.",
        ),
        click.Option(
            ["-k", "expression"],
            metavar="EXPRESSION",
            type=str,
            help="Select tasks via expressions on task ids.",
        ),
    ]
    for command in ("build", "clean", "collect"):
        cli.commands[command].params.extend(additional_build_parameters)


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse marker related options."""
    MARK_GEN.config = config


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    config["markers"] = parse_markers(config["markers"])


@define(slots=True)
class KeywordMatcher:
    """A matcher for keywords.

    Given a list of names, matches any substring of one of these names. The string
    inclusion check is case-insensitive.

    Will match on the name of the task, including the names of its parents. Only matches
    names of items which are either a :class:`Class` or :class:`Function`.

    Additionally, matches on names in the 'extra_keyword_matches' set of any task, as
    well as names directly assigned to test functions.

    """

    _names: AbstractSet[str]

    @classmethod
    def from_task(cls, task: PTask) -> KeywordMatcher:
        mapped_names = {task.name}

        # Add the names attached to the current function through direct assignment.
        mapped_names.update(task.function.__dict__)

        # Add the markers to the keywords as we no longer handle them correctly.
        mapped_names.update(mark.name for mark in task.markers)

        return cls(mapped_names)

    def __call__(self, subname: str) -> bool:
        subname = subname.lower()
        names = (name.lower() for name in self._names)

        return any(subname in name for name in names)


def select_by_keyword(session: Session, dag: nx.DiGraph) -> set[str] | None:
    """Deselect tests by keywords."""
    keywordexpr = session.config["expression"]
    if not keywordexpr:
        return None

    try:
        expression = Expression.compile_(keywordexpr)
    except ParseError as e:
        msg = f"Wrong expression passed to '-k': {keywordexpr}: {e}"
        raise ValueError(msg) from None

    remaining: set[str] = set()
    for task in session.tasks:
        if keywordexpr and expression.evaluate(KeywordMatcher.from_task(task)):
            remaining.update(task_and_preceding_tasks(task.signature, dag))

    return remaining


def select_by_after_keyword(session: Session, after: str) -> set[str]:
    """Select tasks defined by the after keyword."""
    try:
        expression = Expression.compile_(after)
    except ParseError as e:
        msg = f"Wrong expression passed to 'after': {after}: {e}"
        raise ValueError(msg) from None

    ancestors: set[str] = set()
    for task in session.tasks:
        if after and expression.evaluate(KeywordMatcher.from_task(task)):
            ancestors.add(task.signature)

    return ancestors


@define(slots=True)
class MarkMatcher:
    """A matcher for markers which are present.

    Tries to match on any marker names, attached to the given task.

    """

    own_mark_names: set[str]

    @classmethod
    def from_task(cls, task: PTask) -> MarkMatcher:
        mark_names = {mark.name for mark in task.markers}
        return cls(mark_names)

    def __call__(self, name: str) -> bool:
        return name in self.own_mark_names


def select_by_mark(session: Session, dag: nx.DiGraph) -> set[str] | None:
    """Deselect tests by marks."""
    matchexpr = session.config["marker_expression"]
    if not matchexpr:
        return None

    try:
        expression = Expression.compile_(matchexpr)
    except ParseError as e:
        msg = f"Wrong expression passed to '-m': {matchexpr}: {e}"
        raise ValueError(msg) from None

    remaining: set[str] = set()
    for task in session.tasks:
        if expression.evaluate(MarkMatcher.from_task(task)):
            remaining.update(task_and_preceding_tasks(task.signature, dag))

    return remaining


def _deselect_others_with_mark(
    session: Session, remaining: set[str], mark: Mark
) -> None:
    """Deselect tasks."""
    for task in session.tasks:
        if task.signature not in remaining:
            task.markers.append(mark)


def select_tasks_by_marks_and_expressions(session: Session, dag: nx.DiGraph) -> None:
    """Modify the tasks which are executed with expressions and markers."""
    remaining = select_by_keyword(session, dag)
    if remaining is not None:
        _deselect_others_with_mark(
            session, remaining, Mark("skip", (), {"reason": "Deselected by keyword."})
        )
    remaining = select_by_mark(session, dag)
    if remaining is not None:
        _deselect_others_with_mark(
            session, remaining, Mark("skip", (), {"reason": "Deselected by mark."})
        )
