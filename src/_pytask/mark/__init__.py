import sys
import textwrap
import traceback
from typing import AbstractSet

import attr
import click
from _pytask.config import hookimpl
from _pytask.enums import ExitCode
from _pytask.exceptions import ConfigurationError
from _pytask.mark.expression import Expression
from _pytask.mark.expression import ParseError
from _pytask.mark.structures import get_marks_from_obj
from _pytask.mark.structures import get_specific_markers_from_task
from _pytask.mark.structures import has_marker
from _pytask.mark.structures import Mark
from _pytask.mark.structures import MARK_GEN
from _pytask.mark.structures import MarkDecorator
from _pytask.mark.structures import MarkGenerator
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value


__all__ = [
    "get_specific_markers_from_task",
    "get_marks_from_obj",
    "has_marker",
    "Expression",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MARK_GEN",
    "ParseError",
]


@click.command()
def markers(**config_from_cli):
    """Show all registered markers."""
    config_from_cli["command"] = "markers"

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        traceback.print_exception(*sys.exc_info())
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        for name, description in config["markers"].items():
            click.echo(
                textwrap.fill(
                    f"pytask.mark.{name}: {description}", width=config["terminal_width"]
                )
            )
            click.echo("")

    sys.exit(session.exit_code)


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Add marker related options."""
    additional_build_parameters = [
        click.Option(
            ["--strict-markers"],
            is_flag=True,
            help="Raise errors for unknown markers.",
            default=None,
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
    cli.commands["build"].params.extend(additional_build_parameters)
    cli.commands["clean"].params.extend(additional_build_parameters)
    cli.commands["collect"].params.extend(additional_build_parameters)

    cli.add_command(markers)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse marker related options."""
    markers = _read_marker_mapping_from_ini(config_from_file.get("markers", ""))
    config["markers"] = {**markers, **config["markers"]}
    config["strict_markers"] = get_first_non_none_value(
        config,
        config_from_file,
        config_from_cli,
        key="strict_markers",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )

    config["expression"] = config_from_cli.get("expression")
    config["marker_expression"] = config_from_cli.get("marker_expression")

    MARK_GEN.config = config


def _read_marker_mapping_from_ini(string: str) -> dict:
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
    def from_task(cls, task) -> "KeywordMatcher":
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


def deselect_by_keyword(session, tasks) -> None:
    """Deselect tests by keywords."""
    keywordexpr = session.config["expression"]
    if not keywordexpr:
        return

    try:
        expression = Expression.compile_(keywordexpr)
    except ParseError as e:
        raise ValueError(
            f"Wrong expression passed to '-k': {keywordexpr}: {e}"
        ) from None

    remaining = []
    deselected = []
    for task in tasks:
        if keywordexpr and not expression.evaluate(KeywordMatcher.from_task(task)):
            deselected.append(task)
        else:
            remaining.append(task)

    if deselected:
        session.deselected.extend(deselected)
        tasks[:] = remaining


@attr.s(slots=True)
class MarkMatcher:
    """A matcher for markers which are present.

    Tries to match on any marker names, attached to the given colitem.

    """

    own_mark_names = attr.ib()

    @classmethod
    def from_task(cls, task) -> "MarkMatcher":
        mark_names = {mark.name for mark in task.markers}
        return cls(mark_names)

    def __call__(self, name: str) -> bool:
        return name in self.own_mark_names


def deselect_by_mark(session, tasks) -> None:
    """Deselect tests by marks."""
    matchexpr = session.config["marker_expression"]
    if not matchexpr:
        return

    try:
        expression = Expression.compile_(matchexpr)
    except ParseError as e:
        raise ValueError(f"Wrong expression passed to '-m': {matchexpr}: {e}") from None

    remaining = []
    deselected = []
    for task in tasks:
        if expression.evaluate(MarkMatcher.from_task(task)):
            remaining.append(task)
        else:
            deselected.append(task)

    if deselected:
        session.deselected.extend(deselected)
        tasks[:] = remaining


@hookimpl
def pytask_collect_modify_tasks(session, tasks):
    """Modify the list of collected tasks with expressions and markers."""
    deselect_by_keyword(session, tasks)
    deselect_by_mark(session, tasks)
