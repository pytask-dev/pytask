"""This module contains the implementation of ``pytask collect``."""
import sys
import traceback

import click
from _pytask.config import hookimpl
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(collect)


@hookimpl
def pytask_parse_config(config, config_from_cli):
    """Parse configuration."""
    config["nodes"] = config_from_cli.get("nodes", False)


@click.command()
@click.option("--nodes", is_flag=True, help="Show a task's dependencies and products.")
def collect(**config_from_cli):
    """Collect tasks from paths."""
    config_from_cli["command"] = "collect"

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
        traceback.print_exception(*sys.exc_info())

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            dictionary = _organize_tasks(session.tasks)
            _print_collected_tasks(dictionary, session.config["nodes"])

            click.echo("\n" + "=" * config["terminal_width"])

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            traceback.print_exception(*sys.exc_info())

    sys.exit(session.exit_code)


def _organize_tasks(tasks):
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    dictionary = {}
    for task in tasks:
        task_name = task.name.split("::")[1]
        dictionary[task.path] = dictionary.get(task.path, {})

        task_dict = {
            task_name: {
                "depends_on": [node.name for node in task.depends_on.values()],
                "produces": [node.name for node in task.produces.values()],
            }
        }

        dictionary[task.path].update(task_dict)

    return dictionary


def _print_collected_tasks(dictionary, show_nodes):
    """Print the information on collected tasks.

    Parameters
    ----------
    dictionary: dict
        A dictionary with path on the first level, tasks on the second, dependencies and
        products on the third.
    show_nodes: bool
        Indicator for whether dependencies and products should be displayed.

    """
    click.echo("")

    for path in dictionary:
        click.echo(f"<Module {path}>")
        for task in dictionary[path]:
            click.echo(f"  <Function {task}>")
            if show_nodes:
                for dependency in dictionary[path][task]["depends_on"]:
                    click.echo(f"    <Dependency {dependency}>")

                for product in dictionary[path][task]["produces"]:
                    click.echo(f"    <Product {product}>")
