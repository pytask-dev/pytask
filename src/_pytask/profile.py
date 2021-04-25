"""This module contains the code to profile the execution."""
import sys
import time

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.database import db
from _pytask.enums import ColorCode
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.nodes import reduce_node_name
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from pony import orm
from rich.table import Table
from rich.traceback import Traceback


class Runtime(db.Entity):
    """Record of runtimes of tasks."""

    task = orm.PrimaryKey(str)
    date = orm.Required(float)
    duration = orm.Required(float)


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(profile)


@hookimpl(hookwrapper=True)
def pytask_execute_task(task):
    """Attach the duration of the execution to the task."""
    start = time.time()
    yield
    end = time.time()
    task.attributes["duration"] = (start, end)


@hookimpl
def pytask_execute_task_process_report(report):
    task = report.task
    duration = task.attributes.get("duration")
    if report.success and duration is not None:
        _create_or_update_runtime(task.name, *duration)


@orm.db_session
def _create_or_update_runtime(task_name, start, end):
    """Create or update a runtime entry."""
    try:
        runtime = Runtime[task_name]
    except orm.ObjectNotFound:
        Runtime(task=task_name, date=start, duration=end - start)
    else:
        for attr, val in [("date", start), ("duration", end - start)]:
            setattr(runtime, attr, val)


@click.command()
def profile(**config_from_cli):
    """Show profile information on collected tasks."""
    config_from_cli["command"] = "profile"

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED
        console.print(Traceback.from_exception(*sys.exc_info()))

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            tasks = {task.name: task for task in session.tasks}
            tasks = {name: tasks[name] for name in sorted(tasks)}

            runtimes = _collect_runtimes(list(tasks))

            console.print()
            if runtimes:
                table = Table("Task")
                table.add_column("Last Duration (in s)", justify="right")

                for task_name, duration in runtimes.items():
                    reduced_name = reduce_node_name(
                        tasks[task_name], session.config["paths"]
                    )
                    table.add_row(reduced_name, str(round(duration, 2)))

                console.print(table)
            else:
                console.print("No information is stored on the collected tasks.")

            console.rule(style=ColorCode.NEUTRAL)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style=ColorCode.FAILED)

    sys.exit(session.exit_code)


@orm.db_session
def _collect_runtimes(task_names):
    """Collect runtimes."""
    runtimes = [Runtime.get(task=task_name) for task_name in task_names]
    runtimes = [r for r in runtimes if r is not None]
    return {r.task: r.duration for r in runtimes}
