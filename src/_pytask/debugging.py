import functools
import pdb
import sys
import traceback

import click
from _pytask.config import hookimpl
from _pytask.nodes import PythonFunctionTask
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value


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
    config["pdb"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="pdb",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["trace"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="trace",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )


@hookimpl(trylast=True)
def pytask_post_parse(config):
    """Post parse the configuration.

    Register the plugins in this step to let other plugins influence the pdb or trace
    option and may be disable it. Especially thinking about pytask-parallel.

    """
    if config["pdb"]:
        config["pm"].register(PdbDebugger)

    if config["trace"]:
        config["pm"].register(PdbTrace)


class PdbDebugger:
    """Namespace for debugging."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(session, task):
        if isinstance(task, PythonFunctionTask):
            task.function = wrap_function_for_post_mortem_debugging(
                session, task.function
            )
        yield


def wrap_function_for_post_mortem_debugging(session, function):
    """Wrap the function for post-mortem debugging."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        capman = session.config["pm"].get_plugin("capturemanager")
        tm_width = session.config["terminal_width"]
        try:
            function(*args, **kwargs)

        except Exception as e:
            capman.suspend_global_capture(in_=True)
            out, err = capman.read_global_capture()

            if out:
                click.echo(f"{{:-^{tm_width}}}".format(" Captured stdout "))
                sys.stdout.write(out)

            if err:
                click.echo(f"{{:-^{tm_width}}}".format(" Captured stderr "))
                sys.stdout.write(err)

            click.echo(f"{{:>^{tm_width}}}".format(" Traceback: "))
            traceback.print_exc()

            click.echo(f"{{:>^{tm_width}}}".format(" Entering debugger "))

            pdb.post_mortem()

            capman.resume_global_capture()

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
    """Wrap the function for tracing."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        pdb.runcall(function, *args, **kwargs)

    return wrapper
