"""Contains the implementation of ``pytask collect``."""
from __future__ import annotations

import sys
from collections import defaultdict
from typing import Any
from typing import TYPE_CHECKING

import click
from _pytask.click import ColoredCommand
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import create_url_style_for_path
from _pytask.console import FILE_ICON
from _pytask.console import format_task_name
from _pytask.console import PYTHON_ICON
from _pytask.console import TASK_ICON
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import select_by_keyword
from _pytask.mark import select_by_mark
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.outcomes import ExitCode
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.tree_util import tree_leaves
from rich.text import Text
from rich.tree import Tree


if TYPE_CHECKING:
    from pathlib import Path
    from typing import NoReturn


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(collect)


@click.command(cls=ColoredCommand)
@click.option(
    "--nodes",
    is_flag=True,
    default=False,
    help="Show a task's dependencies and products.",
)
def collect(**raw_config: Any | None) -> NoReturn:
    """Collect tasks and report information about them."""
    raw_config["command"] = "collect"

    try:
        # Duplication of the same mechanism in :func:`pytask.build`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED
        console.print_exception()

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.hook.pytask_dag(session=session)

            tasks = _select_tasks_by_expressions_and_marker(session)
            task_with_path = [t for t in tasks if isinstance(t, PTaskWithPath)]

            common_ancestor = _find_common_ancestor_of_all_nodes(
                task_with_path, session.config["paths"], session.config["nodes"]
            )
            dictionary = _organize_tasks(task_with_path)
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
            session.exit_code = ExitCode.DAG_FAILED

        except Exception:  # noqa: BLE001
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    sys.exit(session.exit_code)


def _select_tasks_by_expressions_and_marker(session: Session) -> list[PTask]:
    """Select tasks by expressions and marker."""
    all_tasks = {task.name for task in session.tasks}
    remaining_by_mark = select_by_mark(session, session.dag) or all_tasks
    remaining_by_keyword = select_by_keyword(session, session.dag) or all_tasks
    remaining = remaining_by_mark & remaining_by_keyword

    return [task for task in session.tasks if task.name in remaining]


def _find_common_ancestor_of_all_nodes(
    tasks: list[PTaskWithPath], paths: list[Path], show_nodes: bool
) -> Path:
    """Find common ancestor from all nodes and passed paths."""
    all_paths = []
    for task in tasks:
        all_paths.append(task.path)
        if show_nodes:
            all_paths.extend(
                x.path for x in tree_leaves(task.depends_on) if isinstance(x, PPathNode)
            )
            all_paths.extend(
                x.path for x in tree_leaves(task.produces) if isinstance(x, PPathNode)
            )

    return find_common_ancestor(*all_paths, *paths)


def _organize_tasks(tasks: list[PTaskWithPath]) -> dict[Path, list[PTaskWithPath]]:
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    dictionary: dict[Path, list[PTaskWithPath]] = defaultdict(list)
    for task in tasks:
        dictionary[task.path].append(task)

    sorted_dict = {}
    for k in sorted(dictionary):
        sorted_dict[k] = sorted(dictionary[k], key=lambda x: x.name)

    return sorted_dict


def _print_collected_tasks(
    dictionary: dict[Path, list[PTaskWithPath]],
    show_nodes: bool,
    editor_url_scheme: str,
    common_ancestor: Path,
) -> None:
    """Print the information on collected tasks.

    Parameters
    ----------
    dictionary
        A dictionary with path on the first level, tasks on the second, dependencies and
        products on the third.
    show_nodes
        Indicator for whether dependencies and products should be displayed.
    editor_url_scheme
        The scheme to create an url.
    common_ancestor
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
            reduced_task_name = format_task_name(
                task, editor_url_scheme=editor_url_scheme
            )
            task_branch = module_branch.add(
                Text.assemble(TASK_ICON, "<Function ", reduced_task_name, ">"),
            )

            if show_nodes:
                nodes = list(tree_leaves(task.depends_on))
                sorted_nodes = sorted(nodes, key=lambda x: x.name)
                for node in sorted_nodes:
                    if isinstance(node, PPathNode):
                        if node.path.as_posix() in node.name:
                            reduced_node_name = str(
                                relative_to(node.path, common_ancestor)
                            )
                        else:
                            reduced_node_name = node.name
                        url_style = create_url_style_for_path(
                            node.path, editor_url_scheme
                        )
                        text = Text(reduced_node_name, style=url_style)
                    else:
                        text = node.name

                    task_branch.add(Text.assemble(FILE_ICON, "<Dependency ", text, ">"))

                for node in sorted(
                    tree_leaves(task.produces), key=lambda x: getattr(x, "path", x.name)
                ):
                    if isinstance(node, PPathNode):
                        reduced_node_name = str(relative_to(node.path, common_ancestor))
                        url_style = create_url_style_for_path(
                            node.path, editor_url_scheme
                        )
                        text = Text(reduced_node_name, style=url_style)
                    else:
                        text = Text(node.name)
                    task_branch.add(Text.assemble(FILE_ICON, "<Product ", text, ">"))

    console.print(tree)
