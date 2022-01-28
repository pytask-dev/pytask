"""Implement functionality to collect tasks."""
import inspect
import os
import sys
import time
from importlib import util as importlib_util
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

from _pytask.config import hookimpl
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import console
from _pytask.console import create_summary_panel
from _pytask.console import format_task_id
from _pytask.exceptions import CollectionError
from _pytask.mark_utils import has_marker
from _pytask.nodes import create_task_name
from _pytask.nodes import FilePathNode
from _pytask.nodes import find_duplicates
from _pytask.nodes import MetaTask
from _pytask.nodes import PythonFunctionTask
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import count_outcomes
from _pytask.path import find_case_sensitive_path
from _pytask.report import CollectionReport
from _pytask.session import Session
from _pytask.shared import reduce_node_name
from _pytask.traceback import render_exc_info
from rich.text import Text


@hookimpl
def pytask_collect(session: Session) -> bool:
    """Collect tasks."""
    session.collection_start = time.time()

    _collect_from_paths(session)

    try:
        session.hook.pytask_collect_modify_tasks(session=session, tasks=session.tasks)
    except Exception:
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
        if reports is not None:
            session.collection_reports.extend(reports)
            session.tasks.extend(
                i.node for i in reports if i.outcome == CollectionOutcome.SUCCESS
            )


@hookimpl
def pytask_ignore_collect(path: Path, config: Dict[str, Any]) -> bool:
    """Ignore a path during the collection."""
    is_ignored = any(path.match(pattern) for pattern in config["ignore"])
    return is_ignored


@hookimpl
def pytask_collect_file_protocol(
    session: Session, path: Path, reports: List[CollectionReport]
) -> List[CollectionReport]:
    """Wrap the collection of tasks from a file to collect reports."""
    try:
        reports = session.hook.pytask_collect_file(
            session=session, path=path, reports=reports
        )
    except Exception:
        node = FilePathNode.from_path(path)
        reports = [
            CollectionReport.from_exception(
                outcome=CollectionOutcome.FAIL, node=node, exc_info=sys.exc_info()
            )
        ]

    session.hook.pytask_collect_file_log(session=session, reports=reports)

    return reports


@hookimpl
def pytask_collect_file(
    session: Session, path: Path, reports: List[CollectionReport]
) -> Optional[List[CollectionReport]]:
    """Collect a file."""
    if any(path.match(pattern) for pattern in session.config["task_files"]):
        spec = importlib_util.spec_from_file_location(path.stem, str(path))

        if spec is None:
            raise ImportError(f"Can't find module {path.stem!r} at location {path}.")

        mod = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        collected_reports = []
        for name, obj in inspect.getmembers(mod):
            if has_marker(obj, "parametrize"):
                names_and_objects = session.hook.pytask_parametrize_task(
                    session=session, name=name, obj=obj
                )
            else:
                names_and_objects = [(name, obj)]

            for name_, obj_ in names_and_objects:
                report = session.hook.pytask_collect_task_protocol(
                    session=session, reports=reports, path=path, name=name_, obj=obj_
                )
                if report is not None:
                    collected_reports.append(report)

        return collected_reports
    else:
        return None


@hookimpl
def pytask_collect_task_protocol(
    session: Session, path: Path, name: str, obj: Any
) -> Optional[CollectionReport]:
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
            return CollectionReport.from_node(
                outcome=CollectionOutcome.SUCCESS, node=task
            )

    except Exception:
        task = PythonFunctionTask(name, create_task_name(path, name), path, None)
        return CollectionReport.from_exception(
            outcome=CollectionOutcome.FAIL, exc_info=sys.exc_info(), node=task
        )

    else:
        return None


@hookimpl(trylast=True)
def pytask_collect_task(
    session: Session, path: Path, name: str, obj: Any
) -> Optional[PythonFunctionTask]:
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this `thread
    <https://stackoverflow.com/q/624926/7523785>`_. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if name.startswith("task_") and callable(obj):
        return PythonFunctionTask.from_path_name_function_session(
            path, name, obj, session
        )
    else:
        return None


_TEMPLATE_ERROR: str = (
    "The provided path of the dependency/product in the marker is\n\n{}\n\n, but the "
    "path of the file on disk is\n\n{}\n\nCase-sensitive file systems would raise an "
    "error because the upper and lower case format of the paths does not match.\n\n"
    "Please, align the names to ensure reproducibility on case-sensitive file systems "
    "(often Linux or macOS) or disable this error with 'check_casing_of_paths = false' "
    " in your pytask configuration file.\n\n"
    "Hint: If parts of the path preceding your project directory are not properly "
    "formatted, check whether you need to call `.resolve()` on `SRC`, `BLD` or other "
    "paths created from the `__file__` attribute of a module."
)


@hookimpl(trylast=True)
def pytask_collect_node(
    session: Session, path: Path, node: Union[str, Path]
) -> Optional[FilePathNode]:
    """Collect a node of a task as a :class:`pytask.nodes.FilePathNode`.

    Strings are assumed to be paths. This might be a strict assumption, but since this
    hook is executed at last and possible errors will be shown, it seems reasonable and
    unproblematic.

    ``trylast=True`` might be necessary if other plugins try to parse strings themselves
    like a plugin for downloading files which depends on URLs given as strings.

    Parameters
    ----------
    session : _pytask.session.Session
        The session.
    path : Union[str, pathlib.Path]
        The path to file where the task and node are specified.
    node : Union[str, pathlib.Path]
        The value of the node which can be a str, a path or anything which cannot be
        handled by this function.

    """
    if isinstance(node, str):
        node = Path(node)
    if isinstance(node, Path):
        if not node.is_absolute():
            node = path.parent.joinpath(node)

        # ``normpath`` removes ``../`` from the path which is necessary for the casing
        # check which will fail since ``.resolves()`` also normalizes a path.
        node = Path(os.path.normpath(node))

        if (
            not IS_FILE_SYSTEM_CASE_SENSITIVE
            and session.config["check_casing_of_paths"]
            and sys.platform == "win32"
        ):
            case_sensitive_path = find_case_sensitive_path(node, "win32")
            if str(node) != str(case_sensitive_path):
                raise ValueError(_TEMPLATE_ERROR.format(node, case_sensitive_path))

        return FilePathNode.from_path(node)
    else:
        return None


def _not_ignored_paths(
    paths: Iterable[Path], session: Session
) -> Generator[Path, None, None]:
    """Traverse paths and yield not ignored paths.

    The paths passed by the user can either point to files or directories. For
    directories, all subsequent files and folders are considered, but one level after
    another, so that files of ignored folders are not checked.

    Parameters
    ----------
    paths : List[pathlib.Path]
        List of paths from which tasks are collected.
    session : _pytask.session.Session
        The session.

    Yields
    ------
    path : pathlib.Path
        A path which is not ignored.

    """
    for path in paths:
        if not session.hook.pytask_ignore_collect(path=path, config=session.config):
            if path.is_dir():
                files_in_dir = path.iterdir()
                yield from _not_ignored_paths(files_in_dir, session)
            else:
                yield path


@hookimpl(trylast=True)
def pytask_collect_modify_tasks(tasks: List[MetaTask]) -> None:
    """Given all tasks, assign a short uniquely identifiable name to each task.

    The shorter ids are necessary to display

    """
    id_to_short_id = _find_shortest_uniquely_identifiable_name_for_tasks(tasks)
    for task in tasks:
        short_id = id_to_short_id[task.name]
        task.short_name = short_id


def _find_shortest_uniquely_identifiable_name_for_tasks(
    tasks: List[MetaTask],
) -> Dict[str, str]:
    """Find the shortest uniquely identifiable name for tasks.

    The shortest unique id consists of the module name plus the base name (e.g. function
    name) of the task. If this does not make the id unique, append more and more parent
    folders until the id is unique.

    """
    id_to_short_id = {}

    # Make attempt to add up to twenty parts of the path to ensure uniqueness.
    id_to_task = {task.name: task for task in tasks}
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
    session: Session, reports: List[CollectionReport], tasks: List[PythonFunctionTask]
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
                if isinstance(report.node, MetaTask):
                    short_name = format_task_id(
                        report.node, editor_url_scheme="no_link", short_name=True
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
