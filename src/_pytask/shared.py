"""Functions which are used across various modules."""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Sequence
from typing import TYPE_CHECKING

import click
from _pytask.console import format_task_name
from _pytask.node_protocols import MetaNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to

if TYPE_CHECKING:
    import networkx as nx


def to_list(scalar_or_iter: Any) -> list[Any]:
    """Convert scalars and iterables to list.

    Parameters
    ----------
    scalar_or_iter : Any

    Returns
    -------
    list

    Examples
    --------
    >>> to_list("a")
    ['a']
    >>> to_list(["b"])
    ['b']

    """
    return (
        [scalar_or_iter]
        if isinstance(scalar_or_iter, str) or not isinstance(scalar_or_iter, Sequence)
        else list(scalar_or_iter)
    )


def parse_paths(x: Any | None) -> list[Path] | None:
    """Parse paths."""
    if x is not None:
        paths = [Path(p) for p in to_list(x)]
        paths = [
            Path(p).resolve()
            for path in paths
            for p in glob.glob(path.as_posix())  # noqa: PTH207
        ]
        out = paths
    else:
        out = None
    return out


def reduce_node_name(node: MetaNode, paths: Sequence[Path]) -> str:
    """Reduce the node name.

    The whole name of the node - which includes the drive letter - can be very long
    when using nested folder structures in bigger projects.

    Thus, the part of the name which contains the path is replaced by the relative
    path from one path in ``session.config["paths"]`` to the node.

    """
    if isinstance(node, PPathNode):
        ancestor = find_closest_ancestor(node.path, paths)
        if ancestor is None:
            try:
                ancestor = find_common_ancestor(node.path, *paths)
            except ValueError:
                ancestor = node.path.parents[-1]

        return relative_to(node.path, ancestor).as_posix()
    return node.name


def reduce_names_of_multiple_nodes(
    names: list[str], dag: nx.DiGraph, paths: Sequence[Path]
) -> list[str]:
    """Reduce the names of multiple nodes in the DAG."""
    short_names = []
    for name in names:
        node = dag.nodes[name].get("node") or dag.nodes[name].get("task")

        if isinstance(node, PTask):
            short_name = format_task_name(node, editor_url_scheme="no_link")
        elif isinstance(node, MetaNode):
            short_name = reduce_node_name(node, paths)
        else:
            msg = f"Requires 'Task' or 'Node' and not {type(node)!r}."
            raise TypeError(msg)

        short_names.append(short_name)

    return short_names


def find_duplicates(x: Iterable[Any]) -> set[Any]:
    """Find duplicated entries in iterable.

    Examples
    --------
    >>> find_duplicates(["a", "b", "a"])
    {'a'}
    >>> find_duplicates(["a", "b"])
    set()

    """
    seen = set()
    duplicates = set()

    for i in x:
        if i in seen:
            duplicates.add(i)
        seen.add(i)

    return duplicates


def parse_markers(x: dict[str, str] | list[str] | tuple[str, ...]) -> dict[str, str]:
    """Parse markers."""
    if isinstance(x, (list, tuple)):
        mapping = {name.strip(): "" for name in x}
    elif isinstance(x, dict):
        mapping = {name.strip(): description.strip() for name, description in x.items()}
    else:
        msg = "'markers' must be a mapping from markers to descriptions."
        raise click.BadParameter(msg)

    for name in mapping:
        if not name.isidentifier():
            msg = f"{name} is not a valid Python name and cannot be used as a marker."
            raise click.BadParameter(msg)

    return mapping
