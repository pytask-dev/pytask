import fnmatch
import glob
import importlib
import inspect
import pprint
import sys
import traceback
from pathlib import Path

import click
import pytask
from pytask.exceptions import CollectionError
from pytask.exceptions import TaskDuplicatedError
from pytask.mark_ import has_marker
from pytask.nodes import FilePathNode
from pytask.nodes import PythonFunctionTask
from pytask.report import CollectionReport
from pytask.report import CollectionReportFile
from pytask.report import CollectionReportTask


@pytask.hookimpl
def pytask_collect(session):
    reports = _collect_from_paths(session)
    tasks = _extract_tasks_from_reports(reports)

    try:
        session.hook.pytask_collect_modify_tasks(session=session, tasks=tasks)
    except Exception:
        report = CollectionReport(
            " Modification of collected tasks failed ", sys.exc_info()
        )
        reports.append(report)

    session.hook.pytask_collect_log(session=session, reports=reports, tasks=tasks)

    session.collection_reports = reports
    session.tasks = tasks

    failed_reports = [i for i in reports if not i.successful]
    if failed_reports:
        raise CollectionError

    return True


def _collect_from_paths(session):
    collected_reports = []
    for path in session.config["paths"]:
        paths = (
            path.rglob("*")
            if path.is_dir()
            else [Path(p) for p in glob.glob(path.as_posix())]
        )

        for p in paths:
            ignored = session.hook.pytask_ignore_collect(path=p, config=session.config)

            if not ignored:
                reports = session.hook.pytask_collect_file_protocol(
                    session=session, path=p, reports=collected_reports
                )
                if reports is not None:
                    collected_reports.extend(reports)

    return collected_reports


@pytask.hookimpl
def pytask_ignore_collect(path, config):
    ignored = any(fnmatch.fnmatch(path, pattern) for pattern in config["ignore"])
    return ignored


@pytask.hookimpl
def pytask_collect_file_protocol(session, path, reports):
    try:
        reports = session.hook.pytask_collect_file(
            session=session, path=path, reports=reports
        )
    except Exception:
        exc_info = sys.exc_info()
        reports = [CollectionReportFile.from_exception(path, exc_info)]

    return reports


@pytask.hookimpl
def pytask_collect_file(session, path, reports):
    if path.name.startswith("task_") and path.suffix == ".py":
        spec = importlib.util.spec_from_file_location(path.stem, str(path))

        if spec is None:
            raise ImportError(f"Can't find module {path.stem} at location {path}.")

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


@pytask.hookimpl
def pytask_collect_task_protocol(session, reports, path, name, obj):
    try:
        session.hook.pytask_collect_task_setup(
            session=session, reports=reports, path=path, name=name, obj=obj
        )
        task = session.hook.pytask_collect_task(
            session=session, path=path, name=name, obj=obj
        )
        if task is not None:
            return CollectionReportTask.from_task(task)

    except Exception:
        exc_info = sys.exc_info()
        return CollectionReportTask.from_exception(path, name, exc_info)


@pytask.hookimpl(trylast=True)
def pytask_collect_task_setup(session, reports, path, name):
    paths_to_tasks_w_ident_name = [
        i.path.as_posix()
        for i in reports
        if not isinstance(i, CollectionReportFile) and i.name == name
    ]
    if paths_to_tasks_w_ident_name:
        formatted = pprint.pformat(
            paths_to_tasks_w_ident_name, width=session.config["terminal_width"]
        )
        raise TaskDuplicatedError(
            f"Task '{name}' in '{path}' has the same name as task(s):\n   {formatted}"
        )


@pytask.hookimpl(trylast=True)
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


@pytask.hookimpl(trylast=True)
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
            node = path.parent.joinpath(node).resolve()
        return FilePathNode.from_path(node)


def valid_paths(paths, session):
    """Generate valid paths.

    The paths passed by the user can either point to files or directories. For
    directories, all subsequent files and folders are considered, but one level after
    another, so that files of ignored folders are not checked.

    Parameters
    ----------
    paths : List[pathlib.Path]
        List of paths from which tasks are collected.
    session : pytask.main.Session
        The session.

    """
    for path in paths:
        if not session.hook.pytask_ignore_collect(path=path, config=session.config):
            if path.is_dir():
                files_in_dir = path.glob("*")
                yield from valid_paths(files_in_dir, session)
            else:
                yield path


def _extract_tasks_from_reports(reports):
    return [i.task for i in reports if i.successful]


@pytask.hookimpl
def pytask_collect_log(session, reports, tasks):
    tm_width = session.config["terminal_width"]

    message = f"Collected {len(tasks)} task(s)."
    if session.deselected:
        message += f" Deselected {len(session.deselected)} task(s)."
    click.echo(message)

    failed_reports = [i for i in reports if not i.successful]
    if failed_reports:
        click.echo(f"{{:=^{tm_width}}}".format(" Errors during collection "))

        for report in failed_reports:
            click.echo(f"{{:=^{tm_width}}}".format(report.format_title()))
            traceback.print_exception(*report.exc_info)
            click.echo("")
            click.echo("=" * tm_width)
