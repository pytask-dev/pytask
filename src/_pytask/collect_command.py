"""Contains the implementation of ``pytask collect``."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from typing import NamedTuple
from typing import TYPE_CHECKING

import click
from _pytask.click import ColoredCommand
from _pytask.console import console
from _pytask.console import create_url_style_for_path
from _pytask.console import FILE_ICON
from _pytask.console import format_node_name
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
from _pytask.path import relative_to
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.session import Session
from _pytask.tree_util import tree_leaves
from rich._inspect import Inspect
from rich.text import Text
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import VerticalScroll
from textual.widgets import Header
from textual.widgets import Static
from textual.widgets import Tree

if TYPE_CHECKING:
    from textual.widgets.tree import TreeNode
    from typing import NoReturn
    import networkx as nx


class Task(NamedTuple):
    """A task."""

    task: PTask
    reasons_rerun: list[str]


class Module(NamedTuple):
    """A module with tasks."""

    name: str
    tasks: list[PTask]


class Preview(Static):
    def show_node(self, node: TreeNode) -> None:
        pytask_node = node.data
        if pytask_node is None:
            return
        if hasattr(pytask_node, "__rich_console__"):
            self.update(pytask_node)
        self.update(Inspect(pytask_node, all=False))


class CollectionApp(App):
    """The application for the collect command."""

    CSS = """
    #module-tree {
        content-align: center middle;
        width: 50%;
    }

    Preview {
        content-align: center middle;
    }

    #preview-scroll {
        width: 50%;
    }

    """

    def __init__(self, modules: list[Module]) -> None:
        super().__init__()
        self.modules = modules

    def on_mount(self) -> None:
        from _pytask._version import __version__

        self.title = f"pytask {__version__}"

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree("Modules", id="module-tree")
        tree.root.expand()
        for module in self.modules:
            module_tree = tree.root.add(module.name, expand=False)
            for task in module.tasks:
                task_tree = module_tree.add(task.name, data=task)
                if task.depends_on:
                    dependencies_tree = task_tree.add("Dependencies")
                    for dep in tree_leaves(task.depends_on):
                        dependencies_tree.add_leaf(dep.name, data=dep)
                if task.produces:
                    products_tree = task_tree.add("Products")
                    for prod in tree_leaves(task.produces):
                        products_tree.add_leaf(prod.name, data=prod)

        yield Header()
        with Horizontal():
            yield tree
            yield VerticalScroll(Preview(id="preview"), id="preview-scroll")

    @on(Tree.NodeSelected)
    def update_node(self, event: Tree.NodeSelected) -> None:
        self.query_one("#preview", Preview).show_node(event.node)


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
    pm = storage.get()
    raw_config["command"] = "collect"

    try:
        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):  # pragma: no cover
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)
        console.print_exception()

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.hook.pytask_dag(session=session)

            tasks = _select_tasks_by_expressions_and_marker(session)
            modules = _organize_tasks(tasks)

            import cloudpickle

            with Path("modules.pkl").open("wb") as f:
                cloudpickle.dump(modules, f)

            console.print()
            console.rule(style="neutral")

        except CollectionError:  # pragma: no cover
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:  # pragma: no cover
            session.exit_code = ExitCode.DAG_FAILED

        except Exception:  # noqa: BLE001  # pragma: no cover
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    session.hook.pytask_unconfigure(session=session)
    sys.exit(session.exit_code)


def _select_tasks_by_expressions_and_marker(session: Session) -> list[PTask]:
    """Select tasks by expressions and marker."""
    all_tasks = {task.signature for task in session.tasks}
    remaining_by_mark = select_by_mark(session, session.dag) or all_tasks
    remaining_by_keyword = select_by_keyword(session, session.dag) or all_tasks
    remaining = remaining_by_mark & remaining_by_keyword

    return [task for task in session.tasks if task.signature in remaining]


def _organize_tasks(tasks: list[PTaskWithPath], dag: nx.DiGraph) -> list[Module]:
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    name_to_module = {}
    for task in tasks:
        module = name_to_module.get(
            task.path.as_posix(), Module(task.path.as_posix(), [])
        )
        reasons = _find_reasons_to_rerun(task, dag)
        task_wrap = Task(task=task, reasons_rerun=[])
        module.tasks.append(task)
        name_to_module[module.name] = module
    return [name_to_module[name] for name in sorted(name_to_module)]


def _find_reasons_to_rerun(task: PTask, dag: nx.DiGraph) -> list[str]:
    """Find the reasons to rerun a task."""
    reasons = []
    for task in dag.nodes:
        if node.task == task:
            reasons.append(node.name)
    return reasons


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
                deps = list(tree_leaves(task.depends_on))
                for node in sorted(
                    deps,
                    key=(
                        lambda x: x.path.as_posix()
                        if isinstance(x, PPathNode)
                        else x.name
                    ),
                ):
                    text = format_node_name(node, (common_ancestor,))
                    task_branch.add(Text.assemble(FILE_ICON, "<Dependency ", text, ">"))

                products = list(tree_leaves(task.produces))
                for node in sorted(
                    products,
                    key=lambda x: x.path.as_posix()
                    if isinstance(x, PPathNode)
                    else x.name,
                ):
                    text = format_node_name(node, (common_ancestor,))
                    task_branch.add(Text.assemble(FILE_ICON, "<Product ", text, ">"))

    console.print(tree)
