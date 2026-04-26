"""Implement commands to inspect and update the lockfile."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import click

from _pytask.click import ColoredCommand
from _pytask.click import ColoredGroup
from _pytask.console import console
from _pytask.dag import create_dag
from _pytask.dag_utils import task_and_preceding_tasks
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.lockfile import _build_task_entry
from _pytask.lockfile import _TaskEntry
from _pytask.lockfile import build_portable_task_id
from _pytask.mark import Expression
from _pytask.mark import KeywordMatcher
from _pytask.mark import MarkMatcher
from _pytask.mark import ParseError
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.session import Session
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from collections.abc import Callable

    from _pytask.lockfile import LockfileState


@dataclass(slots=True)
class _PlannedChange:
    task_id: str
    entry: _TaskEntry | None = None

    @property
    def is_accept(self) -> bool:
        return self.entry is not None

    def describe(self) -> str:
        if self.is_accept:
            return f"Accept recorded state for {self.task_id}"
        return f"Remove recorded state for {self.task_id}"


# Task selection.


def _validate_confirmation_options(raw_config: dict[str, Any]) -> None:
    if raw_config["dry_run"] and raw_config["yes"]:
        msg = "The options '--dry-run' and '--yes' are mutually exclusive."
        raise click.UsageError(msg)


def _expression_filter(
    tasks: list[PTask],
    expression: str,
    option: str,
    matcher_from_task: Callable[[PTask], Any],
) -> set[str]:
    try:
        compiled = Expression.compile_(expression)
    except ParseError as e:
        msg = f"Wrong expression passed to {option!r}: {expression}: {e}"
        raise ValueError(msg) from None

    return {
        task.signature for task in tasks if compiled.evaluate(matcher_from_task(task))
    }


def _select_tasks_exact(session: Session) -> list[PTask]:
    selected = {task.signature for task in session.tasks}

    expression = session.config.get("expression")
    if expression:
        selected &= _expression_filter(
            session.tasks, expression, "-k", KeywordMatcher.from_task
        )

    marker_expression = session.config.get("marker_expression")
    if marker_expression:
        selected &= _expression_filter(
            session.tasks, marker_expression, "-m", MarkMatcher.from_task
        )

    return [task for task in session.tasks if task.signature in selected]


def _select_tasks_with_ancestors(session: Session) -> list[PTask]:
    selected = {task.signature for task in _select_tasks_exact(session)}
    selected |= set(
        chain.from_iterable(
            task_and_preceding_tasks(signature, session.dag) for signature in selected
        )
    )
    return [task for task in session.tasks if task.signature in selected]


# Change planning.


def _validate_task_for_accept(session: Session, task: PTask) -> None:
    predecessors = set(session.dag.predecessors(task.signature))

    for node_signature in chain(
        predecessors, [task.signature], session.dag.successors(task.signature)
    ):
        node = session.dag.nodes[node_signature]

        if node_signature not in predecessors and isinstance(node, PProvisionalNode):
            continue

        if isinstance(node, PProvisionalNode):
            msg = (
                f"Task {task.name!r} still references provisional node "
                f"{node.name!r} while accepting lockfile state."
            )
            raise ExecutionError(msg)

        if not isinstance(node, (PTask, PNode)):
            continue

        state = node.state()
        if state is not None:
            continue

        if node_signature in predecessors:
            msg = f"{task.name!r} requires missing node {node.name!r}."
            raise NodeNotFoundError(msg)

        if node_signature == task.signature:
            msg = f"{task.name!r} has no state and cannot be accepted."
            raise ExecutionError(msg)

        msg = f"{task.name!r} is missing product {node.name!r}."
        raise NodeNotFoundError(msg)


def _plan_accept_changes(session: Session) -> list[_PlannedChange]:
    root = session.config["root"]
    planned_changes = []

    for task in _select_tasks_with_ancestors(session):
        _validate_task_for_accept(session, task)
        entry = _build_task_entry(session, task, root)
        if entry is None:
            task_id = build_portable_task_id(task, root)
            msg = f"{task_id!r} has no state and cannot be accepted."
            raise ExecutionError(msg)

        existing = session.config["lockfile_state"].get_task_entry(entry.id)
        if existing != entry:
            planned_changes.append(_PlannedChange(task_id=entry.id, entry=entry))

    return planned_changes


def _plan_reset_changes(session: Session) -> list[_PlannedChange]:
    root = session.config["root"]
    planned_changes = []

    for task in _select_tasks_exact(session):
        task_id = build_portable_task_id(task, root)
        if session.config["lockfile_state"].get_task_entry(task_id) is not None:
            planned_changes.append(_PlannedChange(task_id=task_id))

    return planned_changes


def _plan_clean_changes(session: Session) -> list[_PlannedChange]:
    state: LockfileState = session.config["lockfile_state"]
    current_task_ids = {
        build_portable_task_id(task, session.config["root"]) for task in session.tasks
    }
    stale_ids = state.task_ids() - current_task_ids
    return [_PlannedChange(task_id=task_id) for task_id in sorted(stale_ids)]


# Change application.


def _apply_changes(
    session: Session, planned_changes: list[_PlannedChange]
) -> list[_PlannedChange]:
    if session.config["dry_run"]:
        for change in planned_changes:
            console.print(f"Would {change.describe().lower()}.")
        return planned_changes

    accepted = planned_changes
    if not session.config["yes"]:
        accepted = []
        for change in planned_changes:
            prompt = f"{change.describe()}?"
            if click.confirm(prompt, default=False):
                accepted.append(change)

    if not accepted:
        return []

    state: LockfileState = session.config["lockfile_state"]
    entries = [change.entry for change in accepted if change.entry is not None]
    if entries:
        state.set_task_entries(entries)

    removed_ids = {change.task_id for change in accepted if change.entry is None}
    if removed_ids:
        state.remove_task_entries(removed_ids)

    state.flush()

    for change in accepted:
        console.print(f"{change.describe()}.")

    return accepted


# Command execution.


def _run_lock_command(
    raw_config: dict[str, Any],
    *,
    planner: Callable[[Session], list[_PlannedChange]],
    empty_message: str,
) -> int:
    _validate_confirmation_options(raw_config)
    pm = storage.get()
    from _pytask.cli import DEFAULTS_FROM_CLI  # noqa: PLC0415

    raw_config = cast("dict[str, Any]", DEFAULTS_FROM_CLI) | raw_config
    raw_config["command"] = "lock"

    try:
        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session.from_config(config)
    except (ConfigurationError, Exception):  # noqa: BLE001
        console.print(Traceback(sys.exc_info()))
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)
    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.dag = create_dag(session=session)

            planned_changes = planner(session)

            if planned_changes:
                _apply_changes(session, planned_changes)
            else:
                console.print()
                console.print(empty_message)

            console.print()
            console.rule(style="default")
        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED
            console.rule(style="failed")
        except ResolvingDependenciesError:
            session.exit_code = ExitCode.DAG_FAILED
            console.rule(style="failed")
        except Exception:  # noqa: BLE001
            console.print(Traceback(sys.exc_info()))
            console.rule(style="failed")
            session.exit_code = ExitCode.FAILED

    if hasattr(session.hook, "pytask_unconfigure"):
        session.hook.pytask_unconfigure(session=session)
    return session.exit_code


# Command line interface.


def _add_lock_command_options(
    *, dry_run_help: str
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        func = click.option(
            "--dry-run",
            is_flag=True,
            default=False,
            help=dry_run_help,
        )(func)
        return click.option(
            "-y",
            "--yes",
            is_flag=True,
            default=False,
            help="Apply the changes without prompting for confirmation.",
        )(func)

    return decorator


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(lock)


@click.group(cls=ColoredGroup)
def lock() -> None:
    """Inspect and update recorded task state in the lockfile."""


@lock.command(cls=ColoredCommand)
@_add_lock_command_options(
    dry_run_help="Show which recorded states would be updated without writing changes."
)
def accept(**raw_config: Any) -> None:
    """Accept the current state for selected tasks and their ancestors."""
    sys.exit(
        _run_lock_command(
            raw_config,
            planner=_plan_accept_changes,
            empty_message="No lockfile entries need updating.",
        )
    )


@lock.command(cls=ColoredCommand)
@_add_lock_command_options(
    dry_run_help="Show which recorded states would be removed without writing changes."
)
def reset(**raw_config: Any) -> None:
    """Remove recorded state for selected tasks."""
    sys.exit(
        _run_lock_command(
            raw_config,
            planner=_plan_reset_changes,
            empty_message="No lockfile entries need removing.",
        )
    )


@lock.command(cls=ColoredCommand)
@_add_lock_command_options(
    dry_run_help="Show which stale entries would be removed without writing changes."
)
def clean(**raw_config: Any) -> None:
    """Remove stale lockfile entries which no longer correspond to collected tasks."""
    sys.exit(
        _run_lock_command(
            raw_config,
            planner=_plan_clean_changes,
            empty_message="There are no stale lockfile entries.",
        )
    )
