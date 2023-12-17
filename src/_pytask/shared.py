"""Functions which are used across various modules."""
from __future__ import annotations

import glob
import warnings
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Sequence
from typing import TYPE_CHECKING

import click
from _pytask.console import format_node_name
from _pytask.console import format_task_name
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PTask

if TYPE_CHECKING:
    from enum import Enum
    import networkx as nx


__all__ = [
    "convert_to_enum",
    "find_duplicates",
    "parse_markers",
    "parse_paths",
    "reduce_names_of_multiple_nodes",
    "to_list",
]


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
    if x is None:
        return None

    if isinstance(x, str):
        msg = (
            "Specifying paths as a string in 'pyproject.toml' is deprecated and will "
            "result in an error in v0.5. Please use a list of strings instead: "
            f'["{x}"].'
        )
        warnings.warn(msg, category=FutureWarning, stacklevel=1)
        x = [x]

    paths = [Path(p) for p in to_list(x)]
    for p in paths:
        if not p.exists():
            msg = f"The path '{p}' does not exist."
            raise FileNotFoundError(msg)

    return [
        Path(p).resolve()
        for path in paths
        for p in glob.glob(path.as_posix())  # noqa: PTH207
    ]


def reduce_names_of_multiple_nodes(
    names: list[str], dag: nx.DiGraph, paths: Sequence[Path]
) -> list[str]:
    """Reduce the names of multiple nodes in the DAG."""
    short_names = []
    for name in names:
        node = dag.nodes[name].get("node") or dag.nodes[name].get("task")

        if isinstance(node, PTask):
            short_name = format_task_name(node, editor_url_scheme="no_link").plain
        elif isinstance(node, PNode):
            short_name = format_node_name(node, paths).plain
        else:
            msg = f"Requires a 'PTask' or a 'PNode' and not {type(node)!r}."
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


def convert_to_enum(value: Any, enum: type[Enum]) -> Enum:
    """Convert value to enum."""
    try:
        return enum(value)
    except ValueError:
        values = [e.value for e in enum]
        msg = f"Value {value!r} is not a valid {enum!r}. Valid values are {values}."
        raise ValueError(msg) from None
