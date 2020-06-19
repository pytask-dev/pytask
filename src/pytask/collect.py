import fnmatch
import glob
import importlib
import inspect
import sys
import traceback
from pathlib import Path
from types import FunctionType

import click
import pytask
from pytask.exceptions import CollectionError
from pytask.exceptions import TaskDuplicatedError
from pytask.nodes import FilePathNode
from pytask.nodes import PythonFunctionTask
from pytask.report import CollectionReportFile
from pytask.report import CollectionReportTask


@pytask.hookimpl
def pytask_collect(session):
    _collect_tasks_and_reports(session)
    _extract_tasks_from_reports(session)
    session.hook.pytask_collect_modify_tasks(tasks=session.tasks, config=session.config)
    session.hook.pytask_collect_log(
        reports=session.collection_reports, config=session.config
    )

    return True


def _collect_tasks_and_reports(session):
    session.collection_reports = []
    for path in session.config["paths"]:
        paths = path.rglob("*") if path.is_dir() else [Path(p) for p in glob.glob(path)]

        for p in paths:
            ignored = session.hook.pytask_ignore_collect(path=p, config=session.config)

            if not ignored:
                session.hook.pytask_collect_file_protocol(session=session, path=p)


@pytask.hookimpl
def pytask_ignore_collect(path, config):
    ignored = any(fnmatch.fnmatch(path, pattern) for pattern in config["ignore"])
    return ignored


@pytask.hookimpl
def pytask_collect_file_protocol(session, path):
    try:
        session.hook.pytask_collect_file(session=session, path=path)
    except Exception:
        exc_info = sys.exc_info()
        out = CollectionReportFile.from_exception(path, exc_info)
        session.collection_reports.append(out)


@pytask.hookimpl
def pytask_collect_file(session, path):
    if path.name.startswith("task_") and path.suffix == ".py":
        spec = importlib.util.spec_from_file_location(path.stem, str(path))

        if spec is None:
            raise ImportError(f"Can't find module {path.stem} at location {path}.")

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for name, obj in inspect.getmembers(mod):
            session.hook.pytask_collect_task_protocol(
                session=session, path=path, name=name, obj=obj
            )


@pytask.hookimpl
def pytask_collect_task_protocol(session, path, name, obj):
    try:
        session.hook.pytask_collect_task_setup(
            session=session, path=path, name=name, obj=obj
        )
        task = session.hook.pytask_collect_task(
            session=session, path=path, name=name, obj=obj
        )
    except Exception:
        exc_info = sys.exc_info()
        report = CollectionReportTask.from_exception(path, name, exc_info)
        session.collection_reports.append(report)
        return True
    else:
        if task is not None:
            report = CollectionReportTask.from_task(task)
            session.collection_reports.append(report)
            return True


@pytask.hookimpl(trylast=True)
def pytask_collect_task_setup(session, path, name):
    paths_to_tasks_w_ident_name = [
        i.path.as_posix() for i in session.collection_reports if i.name == name
    ]
    if paths_to_tasks_w_ident_name:
        formatted = ",\n    ".join(paths_to_tasks_w_ident_name)
        raise TaskDuplicatedError(
            f"Task {name} in {path} has the same name as task(s) in:\n   {formatted}"
        )


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
    """Collect a node of a task as a :class:`FilePathNode`.

    Strings are assumed to be paths. This might be a strict assumption, but since this
    hook is attempted at last and possible errors will be shown, it is reasonable and
    unproblematic.

    `trylast=True` might be necessary if other plug-ins try to parse strings themselves
    like a plug-in for downloading files which depends on URLs given as strings.

    Parameters
    ----------
    path : str or pathlib.Path
        The path to file where the task and node are specified.
    node : str or pathlib.Path
        The value of the node which can be a str, a path or anything which cannot be
        handled by this function.

    """
    original_value = node
    if isinstance(node, str):
        node = Path(node)
    if isinstance(node, Path):
        if not node.is_absolute():
            node = path.parent.joinpath(node)
        return FilePathNode.from_path_and_original_value(node, original_value)


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


def _extract_tasks_from_reports(session):
    session.tasks = [i.task for i in session.collection_reports if i.successful]


@pytask.hookimpl
def pytask_collect_log(reports, config):
    failed_reports = [i for i in reports if not i.successful]
    if failed_reports:
        tm_width = config["terminal_width"]
        click.echo(f"{{:=^{tm_width}}}".format(" Errors during collection "))

        for report in failed_reports:
            click.echo(f"{{:=^{tm_width}}}".format(report.format_title()))
            traceback.print_exception(*report.exc_info)
            click.echo("")
            click.echo("=" * tm_width)

        raise CollectionError
