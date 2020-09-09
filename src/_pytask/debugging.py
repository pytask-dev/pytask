import functools
import pdb
import traceback

import click
from _pytask.config import hookimpl
from _pytask.nodes import PythonFunctionTask
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_not_none_value


@hookimpl
def pytask_extend_command_line_interface(cli):
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--pdb"],
            help="Start the interactive debugger on errors.  [default: False]",
            is_flag=True,
            default=None,
        ),
        click.Option(
            ["--trace"],
            help="Enter debugger in the beginning of each task.  [default: False]",
            is_flag=True,
            default=None,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse the configuration."""
    config["pdb"] = get_first_not_none_value(
        config_from_cli,
        config_from_file,
        key="pdb",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["trace"] = get_first_not_none_value(
        config_from_cli,
        config_from_file,
        key="trace",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )


@hookimpl
def pytask_post_parse(config):
    if config["pdb"]:
        config["pm"].register(PdbDebugger)

    if config["trace"]:
        config["pm"].register(PdbTrace)


class PdbDebugger:
    """Namespace for debugging."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(task):
        if isinstance(task, PythonFunctionTask):
            task.function = wrap_function_for_post_mortem_debugging(task.function)
        yield


def wrap_function_for_post_mortem_debugging(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            pdb.post_mortem()
            raise e

    return wrapper


class PdbTrace:
    """Namespace for tracing."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(task):
        if isinstance(task, PythonFunctionTask):
            task.function = wrap_function_for_tracing(task.function)
        yield


def wrap_function_for_tracing(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        pdb.runcall(function, *args, **kwargs)

    return wrapper
