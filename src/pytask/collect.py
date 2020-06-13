import fnmatch
import glob
import itertools
import sys
import traceback
from pathlib import Path
from types import FunctionType

import click
import pytask
from pytask.exceptions import CollectionError
from pytask.nodes import FilePathNode
from pytask.nodes import PythonFunctionTask


@pytask.hookimpl
def pytask_collect(session):
    tasks_and_reports = _collect_tasks_and_reports(session)
    tasks, collection_reports = _separate_tasks_and_reports(tasks_and_reports)
    session.hook.pytask_collect_modify_tasks(tasks=tasks, config=session.config)

    session.tasks = tasks
    session.collection_reports = collection_reports

    session.hook.pytask_collect_log(reports=collection_reports, config=session.config)


def _collect_tasks_and_reports(session):
    tasks_and_reports = []

    for path in session.config["paths"]:
        paths = path.rglob("*") if path.is_dir() else [Path(p) for p in glob.glob(path)]

        for p in paths:
            ignored = session.hook.pytask_ignore_collect(path=p, config=session.config)

            if not ignored:
                collected_ = session.hook.pytask_collect_file(session=session, path=p)
                tasks_and_reports.extend(collected_)

    return tasks_and_reports


@pytask.hookimpl
def pytask_ignore_collect(path, config):
    ignored = any(fnmatch.fnmatch(path, pattern) for pattern in config["ignore"])
    return ignored


@pytask.hookimpl
def pytask_collect_file_protocol(session, path):
    try:
        result = session.hook.pytask_collect_file(session=session, path=path)
    except Exception:
        etype, value, tb = sys.exc_info()
        result = {
            "success": False,
            "path": path,
            "type": etype,
            "value": value,
            "traceback": tb,
        }
    return result


@pytask.hookimpl
def pytask_collect_file(session, path):
    if path.name.startswith("task_") and path.suffix == ".py":
        objects = {"__file__": path.as_posix()}
        exec(compile(path.read_text(), path.as_posix(), "exec"), objects)

        tasks = []
        for name, obj in objects.items():
            task = session.hook.pytask_collect_task_protocol(
                session=session, path=path, name=name, obj=obj
            )
            if task:
                tasks.append(task)

        return tasks


@pytask.hookimpl
def pytask_collect_task_protocol(session, path, name, obj):
    try:
        result = session.hook.pytask_collect_task(
            session=session, path=path, name=name, obj=obj
        )
    except Exception:
        etype, value, tb = sys.exc_info()
        result = {
            "success": False,
            "path": path,
            "name": name,
            "obj": obj,
            "type": etype,
            "value": value,
            "traceback": tb,
        }

    return result


@pytask.hookimpl(trylast=True)
def pytask_collect_task(session, path, name, obj):
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this `thread
    <https://stackoverflow.com/q/624926/7523785>`_. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if name.startswith("task_") and isinstance(obj, FunctionType):
        return PythonFunctionTask.from_path_name_function_session(
            path, name, obj, session
        )


@pytask.hookimpl(trylast=True)
def pytask_collect_node(path, node):
    if isinstance(node, Path):
        if not node.is_absolute():
            node = path.parent.joinpath(node)
        return FilePathNode.from_path(node)


def valid_paths(paths, session):
    """Generate valid paths.

    The paths passed by the user can either point to files or directories. For
    directories, all subsequent files and folders are considered, but one level after
    another, so that files of ignored folders are not checked.

    Parameters
    ----------
    paths : list of pathlib.Path
        List of paths from which tasks are collected.
    session : pytask.main.Session
        The session is explained in :ref:`session`.

    """
    for path in paths:
        if not session.hook.pytask_ignore_collect(path=path, config=session.config):
            if path.is_dir():
                files_in_dir = path.glob("*")
                yield from valid_paths(files_in_dir, session)
            else:
                yield path


def _separate_tasks_and_reports(collected):
    tasks = []
    reports = []

    for outcome in itertools.chain.from_iterable(collected):
        if isinstance(outcome, dict):
            reports.append(outcome)
        else:
            tasks.append(outcome)

    return tasks, reports


@pytask.hookimpl
def pytask_collect_log(reports, config):
    if reports:
        tm_width = config["terminal_width"]
        click.echo(f"{{:=^{tm_width}}}".format(" Errors during collection "))
        click.echo("")

        for result in reports:
            path = result["path"].name
            if "name" in result:
                name = result["name"]
                message = f" Collection of task '{name}' in '{path}' failed "
            else:
                f" Collection of path {path} failed "

            click.echo(f"{{:=^{tm_width}}}".format(message))
            traceback.print_exception(
                result["type"], result["value"], result["traceback"]
            )
            click.echo("")
            click.echo("=" * tm_width)

        raise CollectionError
