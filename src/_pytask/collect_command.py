"""This module contains the implementation of ``pytask collect``."""
import sys
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import create_url_style_for_path
from _pytask.console import FILE_ICON
from _pytask.console import format_task_id
from _pytask.console import PYTHON_ICON
from _pytask.console import TASK_ICON
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import select_by_keyword
from _pytask.mark import select_by_mark
from _pytask.outcomes import ExitCode
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from rich.text import Text
from rich.tree import Tree


if TYPE_CHECKING:
    from typing import NoReturn
    from _pytask.nodes import MetaTask


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(collect)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any], config_from_cli: Dict[str, Any]
) -> None:
    """Parse configuration."""
    config["nodes"] = config_from_cli.get("nodes", False)


@click.command()
@click.option("--nodes", is_flag=True, help="Show a task's dependencies and products.")
def collect(**config_from_cli: Optional[Any]) -> "NoReturn":
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
            session.hook.pytask_resolve_dependencies(session=session)

            tasks = _select_tasks_by_expressions_and_marker(session)

            common_ancestor = _find_common_ancestor_of_all_nodes(
                tasks, session.config["paths"], session.config["nodes"]
            )
            dictionary = _organize_tasks(tasks)
            if dictionary:
                _print_collected_tasks(
                    dictionary,
                    session.config["nodes"],
                    session.config["editor_url_scheme"],
                    common_ancestor,
                )

            console.print()
            console.rule(style="neutral")

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    sys.exit(session.exit_code)


def _select_tasks_by_expressions_and_marker(session: Session) -> "List[MetaTask]":
    """Select tasks by expressions and marker."""
    all_tasks = {task.name for task in session.tasks}
    remaining_by_mark = select_by_mark(session, session.dag) or all_tasks
    remaining_by_keyword = select_by_keyword(session, session.dag) or all_tasks
    remaining = remaining_by_mark & remaining_by_keyword

    return [task for task in session.tasks if task.name in remaining]


def _find_common_ancestor_of_all_nodes(
    tasks: "List[MetaTask]", paths: List[Path], show_nodes: bool
) -> Path:
    """Find common ancestor from all nodes and passed paths."""
    all_paths = []
    for task in tasks:
        all_paths.append(task.path)
        if show_nodes:
            all_paths.extend(
                [
                    node.path
                    for attr in ("depends_on", "produces")
                    for node in getattr(task, attr).values()
                ]
            )

    common_ancestor = find_common_ancestor(*all_paths, *paths)

    return common_ancestor


def _organize_tasks(tasks: List["MetaTask"]) -> Dict[Path, List["MetaTask"]]:
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    dictionary: Dict[Path, List["MetaTask"]] = {}
    for task in tasks:
        dictionary[task.path] = dictionary.get(task.path, [])
        dictionary[task.path].append(task)

    sorted_dict = {}
    for k in sorted(dictionary):
        sorted_dict[k] = sorted(dictionary[k], key=lambda x: x.path)

    return sorted_dict


def _print_collected_tasks(
    dictionary: Dict[Path, List["MetaTask"]],
    show_nodes: bool,
    editor_url_scheme: str,
    common_ancestor: Path,
) -> None:
    """Print the information on collected tasks.

    Parameters
    ----------
    dictionary : Dict[Path, List["MetaTask"]]
        A dictionary with path on the first level, tasks on the second, dependencies and
        products on the third.
    show_nodes : bool
        Indicator for whether dependencies and products should be displayed.
    editor_url_scheme : str
        The scheme to create an url.
    common_ancestor : Path
        The path common to all tasks and nodes.

    """
    # Have a new line between the number of collected tasks and this info.
    console.print()

    tree = Tree("Collected tasks:", highlight=True)

    for module, tasks in dictionary.items():
        reduced_module = relative_to(module, common_ancestor)
        url_style = create_url_style_for_path(module, editor_url_scheme)
        module_branch = tree.add(
            Text.assemble(
                PYTHON_ICON, "<Module ", Text(str(reduced_module), style=url_style), ">"
            )
        )

        for task in tasks:
            reduced_task_name = format_task_id(
                task, editor_url_scheme=editor_url_scheme, relative_to=common_ancestor
            )
            task_branch = module_branch.add(
                Text.assemble(TASK_ICON, "<Function ", reduced_task_name, ">"),
            )

            if show_nodes:
                for node in sorted(task.depends_on.values(), key=lambda x: x.path):
                    reduced_node_name = relative_to(node.path, common_ancestor)
                    url_style = create_url_style_for_path(node.path, editor_url_scheme)
                    task_branch.add(
                        Text.assemble(
                            FILE_ICON,
                            "<Dependency ",
                            Text(str(reduced_node_name), style=url_style),
                            ">",
                        )
                    )

                for node in sorted(task.produces.values(), key=lambda x: x.path):
                    reduced_node_name = relative_to(node.path, common_ancestor)
                    url_style = create_url_style_for_path(node.path, editor_url_scheme)
                    task_branch.add(
                        Text.assemble(
                            FILE_ICON,
                            "<Product ",
                            Text(str(reduced_node_name), style=url_style),
                            ">",
                        )
                    )

    console.print(tree)
