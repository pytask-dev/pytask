import functools
import pdb
import traceback

import click
import pytask
from pytask.config import _get_first_not_none_value
from pytask.nodes import PythonFunctionTask


@pytask.hookimpl
def pytask_add_parameters_to_cli(command):
    additional_parameters = [
        click.Option(["--pdb"], help="Enter debugger on errors.", is_flag=True),
        click.Option(["--trace"], help="Enter debugger at test start.", is_flag=True),
    ]
    command.params.extend(additional_parameters)


@pytask.hookimpl
def pytask_parse_config(config, config_from_cli):
    config["pdb"] = _get_first_not_none_value(config_from_cli, key="pdb", default=False)
    config["trace"] = _get_first_not_none_value(
        config_from_cli, key="trace", default=False
    )


@pytask.hookimpl
def pytask_post_parse(config):
    if config["pdb"]:
        config["pm"].register(PdbDebugger)

    if config["trace"]:
        config["pm"].register(PdbTrace)


class PdbDebugger:
    @staticmethod
    @pytask.hookimpl(hookwrapper=True)
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
    @pytask.hookimpl(hookwrapper=True)
    def pytask_execute_task(task):
        if isinstance(task, PythonFunctionTask):
            task.function = wrap_function_for_tracing(task.function)
        yield


def wrap_function_for_tracing(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        pdb.runcall(function, *args, **kwargs)

    return wrapper
