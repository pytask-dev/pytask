"""This module contains the implementation of ``pytask collect``."""
import sys

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import FILE_ICON
from _pytask.console import PYTHON_ICON
from _pytask.console import TASK_ICON
from _pytask.enums import ColorCode
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.nodes import reduce_node_name
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from rich.tree import Tree


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
        console.print_exception()

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            common_ancestor = _find_common_ancestor_of_all_nodes(
                session.tasks, session.config["paths"]
            )
            dictionary = _organize_tasks(session.tasks, common_ancestor)
            if dictionary:
                _print_collected_tasks(dictionary, session.config["nodes"])

            console.print()
            console.rule(style=ColorCode.NEUTRAL)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style=ColorCode.FAILED)

    sys.exit(session.exit_code)


def _find_common_ancestor_of_all_nodes(tasks, paths):
    """Find common ancestor from all nodes and passed paths."""
    all_paths = []
    for task in tasks:
        all_paths += [task.path] + [
            node.path
            for attr in ("depends_on", "produces")
            for node in getattr(task, attr).values()
        ]

    common_ancestor = find_common_ancestor(*all_paths, *paths)

    return common_ancestor


def _organize_tasks(tasks, common_ancestor):
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    dictionary = {}
    for task in tasks:
        reduced_task_path = relative_to(task.path, common_ancestor)
        reduced_task_name = reduce_node_name(task, [common_ancestor])
        dictionary[reduced_task_path] = dictionary.get(reduced_task_path, {})

        task_dict = {
            reduced_task_name: {
                "depends_on": sorted(
                    relative_to(node.path, common_ancestor)
                    for node in task.depends_on.values()
                ),
                "produces": sorted(
                    relative_to(node.path, common_ancestor)
                    for node in task.produces.values()
                ),
            }
        }

        dictionary[reduced_task_path].update(task_dict)

    dictionary = {key: dictionary[key] for key in sorted(dictionary)}

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
    # Have a new line between the number of collected tasks and this info.
    console.print()

    tree = Tree("Collected tasks:", highlight=True)
    for path in dictionary:
        module_branch = tree.add(PYTHON_ICON + f"<Module {path}>")
        for task in dictionary[path]:
            task_branch = module_branch.add(TASK_ICON + f"<Function {task}>")
            if show_nodes:
                for dependency in dictionary[path][task]["depends_on"]:
                    task_branch.add(FILE_ICON + f"<Dependency {dependency}>")

                for product in dictionary[path][task]["produces"]:
                    task_branch.add(FILE_ICON + f"<Product {product}>")

    console.print(tree)
