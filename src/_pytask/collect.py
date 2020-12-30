"""Implement functionality to collect tasks."""
import importlib
import inspect
import sys
import time
import traceback
from pathlib import Path
from typing import Generator
from typing import List

import click
from _pytask.config import hookimpl
from _pytask.enums import ColorCode
from _pytask.exceptions import CollectionError
from _pytask.mark import has_marker
from _pytask.nodes import FilePathNode
from _pytask.nodes import PythonFunctionTask
from _pytask.nodes import reduce_node_name
from _pytask.report import CollectionReport


@hookimpl
def pytask_collect(session):
    """Collect tasks."""
    session.collection_start = time.time()

    reports = _collect_from_paths(session)
    tasks = _extract_successfully_collected_tasks_from_reports(reports)

    try:
        session.hook.pytask_collect_modify_tasks(session=session, tasks=tasks)
    except Exception:
        report = CollectionReport.from_exception(exc_info=sys.exc_info())
        reports.append(report)

    session.collection_reports = reports
    session.tasks = tasks

    session.hook.pytask_collect_log(
        session=session, reports=session.collection_reports, tasks=session.tasks
    )

    return True


def _collect_from_paths(session):
    """Collect tasks from paths.

    Go through all paths, check if the path is ignored, and collect the file if not.

    """
    collected_reports = session.collection_reports
    for path in _not_ignored_paths(session.config["paths"], session):
        reports = session.hook.pytask_collect_file_protocol(
            session=session, path=path, reports=collected_reports
        )
        if reports is not None:
            collected_reports.extend(reports)

    return collected_reports


@hookimpl
def pytask_ignore_collect(path, config):
    """Ignore a path during the collection."""
    is_ignored = any(path.match(pattern) for pattern in config["ignore"])
    return is_ignored


@hookimpl
def pytask_collect_file_protocol(session, path, reports):
    try:
        reports = session.hook.pytask_collect_file(
            session=session, path=path, reports=reports
        )
    except Exception:
        node = FilePathNode.from_path(path)
        reports = [CollectionReport.from_exception(node=node, exc_info=sys.exc_info())]

    return reports


@hookimpl
def pytask_collect_file(session, path, reports):
    """Collect a file."""
    if any(path.match(pattern) for pattern in session.config["task_files"]):
        spec = importlib.util.spec_from_file_location(path.stem, str(path))

        if spec is None:
            raise ImportError(f"Can't find module '{path.stem}' at location {path}.")

        mod = importlib.util.module_from_spec(spec)
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


@hookimpl
def pytask_collect_task_protocol(session, path, name, obj):
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
            return CollectionReport.from_node(task)

    except Exception:
        return CollectionReport.from_exception(
            exc_info=sys.exc_info(), node=locals().get("task")
        )


@hookimpl(trylast=True)
def pytask_collect_task(session, path, name, obj):
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this `thread
    <https://stackoverflow.com/q/624926/7523785>`_. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if name.startswith("task_") and callable(obj):
        return PythonFunctionTask.from_path_name_function_session(
            path, name, obj, session
        )


@hookimpl(trylast=True)
def pytask_collect_node(path, node):
    """Collect a node of a task as a :class:`pytask.nodes.FilePathNode`.

    Strings are assumed to be paths. This might be a strict assumption, but since this
    hook is attempted at last and possible errors will be shown, it is reasonable and
    unproblematic.

    ``trylast=True`` might be necessary if other plugins try to parse strings themselves
    like a plugin for downloading files which depends on URLs given as strings.

    Parameters
    ----------
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
        return FilePathNode.from_path(node)


def _not_ignored_paths(paths: List[Path], session) -> Generator[Path, None, None]:
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


def _extract_successfully_collected_tasks_from_reports(reports):
    """Extract successfully collected tasks from reports."""
    return [i.node for i in reports if i.successful]


@hookimpl
def pytask_collect_log(session, reports, tasks):
    """Log collection."""
    session.collection_end = time.time()
    tm_width = session.config["terminal_width"]

    message = f"Collected {len(tasks)} task{'' if len(tasks) == 1 else 's'}."

    n_deselected = len(session.deselected)
    if n_deselected:
        message += f" Deselected {n_deselected} task{'' if n_deselected == 1 else 's'}."
    click.echo(message)

    failed_reports = [i for i in reports if not i.successful]
    if failed_reports:
        click.echo("")
        click.echo(f"{{:=^{tm_width}}}".format(" Failures during collection "))

        for report in failed_reports:
            if report.node is None:
                header = " Error "
            else:
                short_name = reduce_node_name(report.node, session.config["paths"])
                header = f" Could not collect {short_name} "

            click.echo(f"{{:_^{tm_width}}}".format(header))

            click.echo("")

            traceback.print_exception(*report.exc_info)

            click.echo("")

        session.hook.pytask_log_session_footer(
            session=session,
            infos=[
                (len(tasks), "collected", ColorCode.SUCCESS),
                (len(failed_reports), "failed", ColorCode.FAILED),
                (n_deselected, "deselected", ColorCode.NEUTRAL),
            ],
            duration=round(session.collection_end - session.collection_start, 2),
            color=ColorCode.FAILED if len(failed_reports) else ColorCode.SUCCESS,
            terminal_width=session.config["terminal_width"],
        )

        raise CollectionError
