from __future__ import annotations

from pathlib import Path
from typing import ClassVar
from typing import NamedTuple
from typing import TYPE_CHECKING

import cloudpickle
from _pytask.tree_util import tree_leaves
from rich.console import RenderableType
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import VerticalScroll
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Static
from textual.widgets import Tree

if TYPE_CHECKING:
    from textual.widgets.tree import TreeNode
    from _pytask.node_protocols import PTask


class Module(NamedTuple):
    """A module with tasks."""

    name: str
    tasks: list[PTask]


class Preview(Static):
    def show_node(self, node: TreeNode) -> None:
        pytask_node = node.data
        if pytask_node is None:
            self.update("")
            return
        if isinstance(pytask_node, RenderableType):
            self.update(pytask_node)
        # self.update(Inspect(pytask_node, all=False))


class CollectionApp(App):
    """The application for the collect command."""

    BINDINGS: ClassVar = [Binding("ctrl+c", "quit", "Quit", key_display="ctrl+c")]
    CSS_PATH: str = "app.css"

    def __init__(self) -> None:
        super().__init__()
        with Path("modules.pkl").open("rb") as f:
            self.modules = cloudpickle.load(f)

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
            yield Footer()

    @on(Tree.NodeSelected)
    def update_node(self, event: Tree.NodeSelected) -> None:
        self.query_one("#preview", Preview).show_node(event.node)


if __name__ == "__main__":
    app = CollectionApp()
    app.run()
