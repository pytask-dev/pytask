"""Implement functionality to collect tasks."""
from __future__ import annotations

import inspect
import itertools
import os
import sys
import time
from pathlib import Path
from typing import Any
from typing import Generator
from typing import Iterable
from typing import TYPE_CHECKING

from _pytask.collect_utils import parse_dependencies_from_task_function
from _pytask.collect_utils import parse_products_from_task_function
from _pytask.config import hookimpl
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import console
from _pytask.console import create_summary_panel
from _pytask.console import format_task_name
from _pytask.console import get_file
from _pytask.console import is_jupyter
from _pytask.exceptions import CollectionError
from _pytask.mark_utils import has_mark
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.nodes import PathNode
from _pytask.nodes import PythonNode
from _pytask.nodes import Task
from _pytask.nodes import TaskWithoutPath
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import count_outcomes
from _pytask.path import find_case_sensitive_path
from _pytask.path import import_path
from _pytask.report import CollectionReport
from _pytask.shared import find_duplicates
from _pytask.shared import reduce_node_name
from _pytask.task_utils import task as task_decorator
from _pytask.traceback import render_exc_info
from rich.text import Text

if TYPE_CHECKING:
    from _pytask.session import Session
    from _pytask.models import NodeInfo


@hookimpl
def pytask_collect(session: Session) -> bool:
    """Collect tasks."""
    session.collection_start = time.time()

    _collect_from_paths(session)
    _collect_from_tasks(session)

    session.tasks.extend(
        i.node
        for i in session.collection_reports
        if i.outcome == CollectionOutcome.SUCCESS and isinstance(i.node, PTask)
    )

    try:
        session.hook.pytask_collect_modify_tasks(session=session, tasks=session.tasks)
    except Exception:  # noqa: BLE001
        report = CollectionReport.from_exception(
            outcome=CollectionOutcome.FAIL, exc_info=sys.exc_info()
        )
        session.collection_reports.append(report)

    session.hook.pytask_collect_log(
        session=session, reports=session.collection_reports, tasks=session.tasks
    )

    return True


def _collect_from_paths(session: Session) -> None:
    """Collect tasks from paths.

    Go through all paths, check if the path is ignored, and collect the file if not.

    """
    for path in _not_ignored_paths(session.config["paths"], session):
        reports = session.hook.pytask_collect_file_protocol(
            session=session, path=path, reports=session.collection_reports
        )

        if reports:
            session.collection_reports.extend(reports)


def _collect_from_tasks(session: Session) -> None:
    """Collect tasks from user provided tasks via the functional interface."""
    for raw_task in session.config.get("tasks", ()):
        if isinstance(raw_task, PTask):
            report = session.hook.pytask_collect_task_protocol(
                session=session,
                reports=session.collection_reports,
                path=None,
                name=None,
                obj=raw_task,
            )

        if callable(raw_task):
            if not hasattr(raw_task, "pytask_meta"):
                raw_task = task_decorator()(raw_task)  # noqa: PLW2901

            try:
                path = get_file(raw_task)
            except (TypeError, OSError):
                path = None
            else:
                if path.name == "<stdin>":
                    path = None  # pragma: no cover

            # Detect whether a path is defined in a Jupyter notebook.
            if is_jupyter() and "ipykernel" in path.as_posix() and path.suffix == ".py":
                path = None  # pragma: no cover

            name = raw_task.pytask_meta.name

        # When a task is not a PTask and a callable, set arbitrary values and it will
        # pass without errors and not collected.
        else:
            name = ""
            path = None

        report = session.hook.pytask_collect_task_protocol(
            session=session,
            reports=session.collection_reports,
            path=path,
            name=name,
            obj=raw_task,
        )

        if report is not None:
            session.collection_reports.append(report)


@hookimpl
def pytask_ignore_collect(path: Path, config: dict[str, Any]) -> bool:
    """Ignore a path during the collection."""
    return any(path.match(pattern) for pattern in config["ignore"])


@hookimpl
def pytask_collect_file_protocol(
    session: Session, path: Path, reports: list[CollectionReport]
) -> list[CollectionReport]:
    """Wrap the collection of tasks from a file to collect reports."""
    try:
        new_reports = session.hook.pytask_collect_file(
            session=session, path=path, reports=reports
        )
        flat_reports = list(itertools.chain.from_iterable(new_reports))
    except Exception:  # noqa: BLE001
        node = PathNode.from_path(path)
        flat_reports = [
            CollectionReport.from_exception(
                outcome=CollectionOutcome.FAIL, node=node, exc_info=sys.exc_info()
            )
        ]

    session.hook.pytask_collect_file_log(session=session, reports=flat_reports)

    return flat_reports


@hookimpl
def pytask_collect_file(
    session: Session, path: Path, reports: list[CollectionReport]
) -> list[CollectionReport] | None:
    """Collect a file."""
    if any(path.match(pattern) for pattern in session.config["task_files"]):
        mod = import_path(path, session.config["root"])

        collected_reports = []
        for name, obj in inspect.getmembers(mod):
            # Ensures that tasks with this decorator are only collected once.
            if has_mark(obj, "task"):
                continue

            report = session.hook.pytask_collect_task_protocol(
                session=session, reports=reports, path=path, name=name, obj=obj
            )
            if report is not None:
                collected_reports.append(report)

        return collected_reports
    return None


@hookimpl
def pytask_collect_task_protocol(
    session: Session, path: Path | None, name: str, obj: Any
) -> CollectionReport | None:
    """Start protocol for collecting a task."""
    try:
        session.hook.pytask_collect_task_setup(
            session=session, path=path, name=name, obj=obj
        )
        task = session.hook.pytask_collect_task(
            session=session, path=path, name=name, obj=obj
        )
        if task is not None:
            session.hook.pytask_collect_task_teardown(session=session, task=task)
            return CollectionReport(outcome=CollectionOutcome.SUCCESS, node=task)

    except Exception:  # noqa: BLE001
        task = Task(base_name=name, path=path, function=None)
        return CollectionReport.from_exception(
            outcome=CollectionOutcome.FAIL, exc_info=sys.exc_info(), node=task
        )

    else:
        return None


@hookimpl(trylast=True)
def pytask_collect_task(
    session: Session, path: Path, name: str, obj: Any
) -> PTask | None:
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this thread:
    https://stackoverflow.com/q/624926/7523785. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if (name.startswith("task_") or has_mark(obj, "task")) and callable(obj):
        path_nodes = Path.cwd() if path is None else path.parent
        dependencies = parse_dependencies_from_task_function(
            session, path_nodes, name, obj
        )
        products = parse_products_from_task_function(session, path_nodes, name, obj)

        markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []

        # Get the underlying function to avoid having different states of the function,
        # e.g. due to pytask_meta, in different layers of the wrapping.
        unwrapped = inspect.unwrap(obj)

        if path is None:
            return TaskWithoutPath(
                name=name,
                function=unwrapped,
                depends_on=dependencies,
                produces=products,
                markers=markers,
            )
        return Task(
            base_name=name,
            path=path,
            function=unwrapped,
            depends_on=dependencies,
            produces=products,
            markers=markers,
        )
    if isinstance(obj, PTask):
        return obj
    return None


_TEMPLATE_ERROR: str = """\
The provided path of the dependency/product is

{}

, but the path of the file on disk is

{}

Case-sensitive file systems would raise an error because the upper and lower case \
format of the paths does not match.

Please, align the names to ensure reproducibility on case-sensitive file systems \
(often Linux or macOS) or disable this error with 'check_casing_of_paths = false' in \
your pytask configuration file.

Hint: If parts of the path preceding your project directory are not properly \
formatted, check whether you need to call `.resolve()` on `SRC`, `BLD` or other paths \
created from the `__file__` attribute of a module.
"""


@hookimpl(trylast=True)
def pytask_collect_node(session: Session, path: Path, node_info: NodeInfo) -> PNode:
    """Collect a node of a task as a :class:`pytask.nodes.PathNode`.

    Strings are assumed to be paths. This might be a strict assumption, but since this
    hook is executed at last and possible errors will be shown, it seems reasonable and
    unproblematic.

    ``trylast=True`` might be necessary if other plugins try to parse strings themselves
    like a plugin for downloading files which depends on URLs given as strings.

    Parameters
    ----------
    path
        The path helps if the path of the node is given relative to the task. The path
        either points to the parent directory of the task module or to the current
        working directory for tasks defined in the REPL or in Jupyter notebooks.

    """
    node = node_info.value

    if isinstance(node, PythonNode):
        if not node.name:
            suffix = "-" + "-".join(map(str, node_info.path)) if node_info.path else ""
            node.name = node_info.arg_name + suffix
        return node

    if isinstance(node, PPathNode) and not node.path.is_absolute():
        node.path = path.joinpath(node.path)

        # ``normpath`` removes ``../`` from the path which is necessary for the casing
        # check which will fail since ``.resolves()`` also normalizes a path.
        node.path = Path(os.path.normpath(node.path))
        _raise_error_if_casing_of_path_is_wrong(
            node.path, session.config["check_casing_of_paths"]
        )

    if isinstance(node, PNode):
        return node

    if isinstance(node, Path):
        if not node.is_absolute():
            node = path.joinpath(node)

        # ``normpath`` removes ``../`` from the path which is necessary for the casing
        # check which will fail since ``.resolves()`` also normalizes a path.
        node = Path(os.path.normpath(node))
        _raise_error_if_casing_of_path_is_wrong(
            node, session.config["check_casing_of_paths"]
        )
        return PathNode.from_path(node)

    suffix = "-" + "-".join(map(str, node_info.path)) if node_info.path else ""
    node_name = node_info.arg_name + suffix
    return PythonNode(value=node, name=node_name)


def _raise_error_if_casing_of_path_is_wrong(
    path: Path, check_casing_of_paths: bool
) -> None:
    """Raise an error if the path does not have the correct casing."""
    if (
        not IS_FILE_SYSTEM_CASE_SENSITIVE
        and sys.platform == "win32"
        and check_casing_of_paths
    ):
        case_sensitive_path = find_case_sensitive_path(path, "win32")
        if str(path) != str(case_sensitive_path):
            raise ValueError(_TEMPLATE_ERROR.format(path, case_sensitive_path))


def _not_ignored_paths(
    paths: Iterable[Path], session: Session
) -> Generator[Path, None, None]:
    """Traverse paths and yield not ignored paths.

    The paths passed by the user can either point to files or directories. For
    directories, all subsequent files and folders are considered, but one level after
    another, so that files of ignored folders are not checked.

    """
    for path in paths:
        if not session.hook.pytask_ignore_collect(path=path, config=session.config):
            if path.is_dir():
                files_in_dir = path.iterdir()
                yield from _not_ignored_paths(files_in_dir, session)
            else:
                yield path


@hookimpl(trylast=True)
def pytask_collect_modify_tasks(tasks: list[PTask]) -> None:
    """Given all tasks, assign a short uniquely identifiable name to each task."""
    id_to_short_id = _find_shortest_uniquely_identifiable_name_for_tasks(tasks)
    for task in tasks:
        if task.name in id_to_short_id and isinstance(task, Task):
            task.display_name = id_to_short_id[task.name]


def _find_shortest_uniquely_identifiable_name_for_tasks(
    tasks: list[PTask],
) -> dict[str, str]:
    """Find the shortest uniquely identifiable name for tasks.

    The shortest unique id consists of the module name plus the base name (e.g. function
    name) of the task. If this does not make the id unique, append more and more parent
    folders until the id is unique.

    """
    id_to_short_id = {}

    # Make attempt to add up to twenty parts of the path to ensure uniqueness.
    id_to_task = {task.name: task for task in tasks if isinstance(task, Task)}
    for n_parts in range(1, 20):
        dupl_id_to_short_id = {
            id_: "/".join(task.path.parts[-n_parts:]) + "::" + task.base_name
            for id_, task in id_to_task.items()
        }
        duplicates = find_duplicates(dupl_id_to_short_id.values())

        for id_, short_id in dupl_id_to_short_id.items():
            if short_id not in duplicates:
                id_to_short_id[id_] = short_id
                id_to_task.pop(id_)

    # If there are still non-unique task ids, just use the full id as the short id.
    for id_, task in id_to_task.items():
        id_to_short_id[id_] = task.name

    return id_to_short_id


@hookimpl
def pytask_collect_log(
    session: Session, reports: list[CollectionReport], tasks: list[PTask]
) -> None:
    """Log collection."""
    session.collection_end = time.time()

    console.print(f"Collected {len(tasks)} task{'' if len(tasks) == 1 else 's'}.")

    failed_reports = [r for r in reports if r.outcome == CollectionOutcome.FAIL]
    if failed_reports:
        counts = count_outcomes(reports, CollectionOutcome)

        console.print()
        console.rule(
            Text("Failures during collection", style=CollectionOutcome.FAIL.style),
            style=CollectionOutcome.FAIL.style,
        )

        for report in failed_reports:
            if report.node is None:
                header = "Error"
            else:
                if isinstance(report.node, PTask):
                    short_name = format_task_name(
                        report.node, editor_url_scheme="no_link"
                    )
                else:
                    short_name = reduce_node_name(report.node, session.config["paths"])
                header = f"Could not collect {short_name}"

            console.rule(
                Text(header, style=CollectionOutcome.FAIL.style),
                style=CollectionOutcome.FAIL.style,
            )

            console.print()

            console.print(
                render_exc_info(*report.exc_info, session.config["show_locals"])
            )

            console.print()

        panel = create_summary_panel(
            counts, CollectionOutcome, "Collected errors and tasks"
        )
        console.print(panel)

        session.hook.pytask_log_session_footer(
            session=session,
            duration=session.collection_end - session.collection_start,
            outcome=CollectionOutcome.FAIL
            if counts[CollectionOutcome.FAIL]
            else CollectionOutcome.SUCCESS,
        )

        raise CollectionError
