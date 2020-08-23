import functools
import pdb
import traceback

import click
from _pytask.config import hookimpl
from _pytask.nodes import PythonFunctionTask
from _pytask.shared import get_first_not_none_value


@hookimpl
def pytask_extend_command_line_interface(cli):
    additional_parameters = [
        click.Option(
            ["--pdb"], help="Enter debugger on errors.", is_flag=True, default=None
        ),
        click.Option(
            ["--trace"],
            help="Enter debugger when starting each task.",
            is_flag=True,
            default=None,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    config["pdb"] = get_first_not_none_value(
        config_from_cli, config_from_file, key="pdb", default=False
    )
    config["trace"] = get_first_not_none_value(
        config_from_cli, config_from_file, key="trace", default=False
    )


@hookimpl
def pytask_post_parse(config):
    if config["pdb"]:
        config["pm"].register(PdbDebugger)

    if config["trace"]:
        config["pm"].register(PdbTrace)


class PdbDebugger:
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
