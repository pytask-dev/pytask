from __future__ import annotations

import sys
from typing import AbstractSet
from typing import Any
from typing import Set
from typing import TYPE_CHECKING

import attr
import click
import networkx as nx
from _pytask.attrs import convert_to_none_or_type
from _pytask.config import hookimpl
from _pytask.config_utils import Configuration
from _pytask.config_utils import merge_settings
from _pytask.console import console
from _pytask.dag import task_and_preceding_tasks
from _pytask.exceptions import ConfigurationError
from _pytask.mark.expression import Expression
from _pytask.mark.expression import ParseError
from _pytask.mark.structures import Mark
from _pytask.mark.structures import MARK_GEN
from _pytask.mark.structures import MarkDecorator
from _pytask.mark.structures import MarkGenerator
from _pytask.nodes import Task
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.typed_settings import option
from rich.table import Table


if TYPE_CHECKING:
    from typing import NoReturn


__all__ = [
    "Expression",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MARK_GEN",
    "ParseError",
]


def markers(paths, main_settings, markers_settings) -> NoReturn:
    """Show all registered markers."""
    config = merge_settings(paths, main_settings, markers_settings, "markers")

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        console.print_exception()
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        table = Table("Marker", "Description", leading=1)

        for name, description in config.option.markers.items():
            table.add_row(f"pytask.mark.{name}", description)

        console.print(table)

    sys.exit(session.exit_code)


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Add marker related options."""
    for command in ("build", "clean", "collect"):
        if command in ("clean", "collect"):
            continue
        cli["build"]["options"] = {
            **cli["build"]["options"],
            "strict_markers": option(
                type=bool,
                default=True,
                is_flag=True,
                help="Raise errors for unknown markers.",
            ),
            "expression": option(
                converter=convert_to_none_or_type(str),
                default=None,
                help="Select tasks via expressions on task ids.",
                param_decls="-k",
                metavar="EXPRESSION",
                type=str,
            ),
            "marker_expression": option(
                converter=convert_to_none_or_type(str),
                default=None,
                help="Select tasks via marker expressions.",
                param_decls="-m",
                metavar="MARKER_EXPRESSION",
                type=str,
            ),
        }

    cli["markers"] = {"cmd": markers, "options": {}}


@hookimpl(trylast=True)
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse marker related options."""
    markers = config.get_all("markers")
    merged_markers = {k: v for m in reversed(markers) for k, v in m.items()}
    config.attrs["markers"] = {k: merged_markers[k] for k in sorted(merged_markers)}


@hookimpl
def pytask_post_parse(config):
    MARK_GEN.config = config


def _read_marker_mapping_from_ini(string: str) -> dict[str, str]:
    """Read marker descriptions from configuration file."""
    # Split by newlines and remove empty strings.
    lines = filter(lambda x: bool(x), string.split("\n"))
    mapping = {}
    for line in lines:
        try:
            key, value = line.split(":")
        except ValueError as e:
            key = line
            value = ""
            if not key.isidentifier():
                raise ValueError(
                    f"{key} is not a valid Python name and cannot be used as a marker."
                ) from e

        mapping[key] = value

    return mapping


@attr.s(slots=True)
class KeywordMatcher:
    """A matcher for keywords.

    Given a list of names, matches any substring of one of these names. The string
    inclusion check is case-insensitive.

    Will match on the name of the task, including the names of its parents. Only matches
    names of items which are either a :class:`Class` or :class:`Function`.

    Additionally, matches on names in the 'extra_keyword_matches' set of any task, as
    well as names directly assigned to test functions.

    """

    _names = attr.ib(type=AbstractSet[str])

    @classmethod
    def from_task(cls, task: Task) -> KeywordMatcher:
        mapped_names = {task.name}

        # Add the names attached to the current function through direct assignment.
        function_obj = task.function
        if function_obj:
            mapped_names.update(function_obj.__dict__)

        # Add the markers to the keywords as we no longer handle them correctly.
        mapped_names.update(mark.name for mark in task.markers)

        return cls(mapped_names)

    def __call__(self, subname: str) -> bool:
        subname = subname.lower()
        names = (name.lower() for name in self._names)

        for name in names:
            if subname in name:
                return True
        return False


def select_by_keyword(session: Session, dag: nx.DiGraph) -> set[str]:
    """Deselect tests by keywords."""
    keywordexpr = session.config.option.expression
    if not keywordexpr:
        return None

    try:
        expression = Expression.compile_(keywordexpr)
    except ParseError as e:
        raise ValueError(
            f"Wrong expression passed to '-k': {keywordexpr}: {e}"
        ) from None

    remaining: set[str] = set()
    for task in session.tasks:
        if keywordexpr and expression.evaluate(KeywordMatcher.from_task(task)):
            remaining.update(task_and_preceding_tasks(task.name, dag))

    return remaining


@attr.s(slots=True)
class MarkMatcher:
    """A matcher for markers which are present.

    Tries to match on any marker names, attached to the given task.

    """

    own_mark_names = attr.ib(type=Set[str])

    @classmethod
    def from_task(cls, task: Task) -> MarkMatcher:
        mark_names = {mark.name for mark in task.markers}
        return cls(mark_names)

    def __call__(self, name: str) -> bool:
        return name in self.own_mark_names


def select_by_mark(session: Session, dag: nx.DiGraph) -> set[str]:
    """Deselect tests by marks."""
    matchexpr = session.config.option.marker_expression
    if not matchexpr:
        return None

    try:
        expression = Expression.compile_(matchexpr)
    except ParseError as e:
        raise ValueError(f"Wrong expression passed to '-m': {matchexpr}: {e}") from None

    remaining: set[str] = set()
    for task in session.tasks:
        if expression.evaluate(MarkMatcher.from_task(task)):
            remaining.update(task_and_preceding_tasks(task.name, dag))

    return remaining


def _deselect_others_with_mark(
    session: Session, remaining: set[str], mark: Mark
) -> None:
    for task in session.tasks:
        if task.name not in remaining:
            task.markers.append(mark)


@hookimpl
def pytask_resolve_dependencies_modify_dag(session: Session, dag: nx.DiGraph) -> None:
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
