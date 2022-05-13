"""Functions which are used across various modules."""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Sequence

import networkx as nx
from _pytask.console import format_task_id
from _pytask.nodes import MetaNode
from _pytask.nodes import Task
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to


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
            Path(p).resolve() for path in paths for p in glob.glob(path.as_posix())
        ]
        out = paths
    else:
        out = None
    return out


def falsy_to_none_callback(
    ctx: Any, param: Any, value: Any  # noqa: U100
) -> Any | None:
    """Convert falsy object to ``None``.

    Some click arguments accept multiple inputs and instead of ``None`` as a default if
    no information is passed, they return empty lists or tuples.

    Since pytask uses ``None`` as a placeholder value for skippable inputs, convert the
    values.

    Examples
    --------
    >>> falsy_to_none_callback(None, None, ()) is None
    True
    >>> falsy_to_none_callback(None, None, []) is None
    True
    >>> falsy_to_none_callback(None, None, 1)
    1

    """
    return value if value else None


def get_first_non_none_value(
    *configs: dict[str, Any],
    key: str,
    default: Any | None = None,
    callback: Callable[..., Any] | None = None,
) -> Any:
    """Get the first non-None value for a key from a list of dictionaries.

    This function allows to prioritize information from many configurations by changing
    the order of the inputs while also providing a default.

    Examples
    --------
    >>> get_first_non_none_value({"a": None}, {"a": 1}, key="a")
    1
    >>> get_first_non_none_value({"a": None}, {"a": None}, key="a", default="default")
    'default'
    >>> get_first_non_none_value({}, {}, key="a", default="default")
    'default'
    >>> get_first_non_none_value({"a": None}, {"a": "b"}, key="a")
    'b'

    """
    callback = (lambda x: x) if callback is None else callback  # noqa: E731
    processed_values = (callback(config.get(key)) for config in configs)
    return next((value for value in processed_values if value is not None), default)


def parse_value_or_multiline_option(value: str | None) -> None | str | list[str]:
    """Parse option which can hold a single value or values separated by new lines."""
    if value in ["none", "None", None, ""]:
        return None
    elif isinstance(value, (list, tuple)):
        return list(map(str, value))
    elif isinstance(value, str) and "\n" in value:
        return [v.strip() for v in value.split("\n") if v.strip()]
    elif isinstance(value, str):
        return value.strip()
    else:
        raise ValueError(f"Input {value!r} is neither a 'str' nor 'None'.")


def convert_truthy_or_falsy_to_bool(x: bool | str | None) -> bool:
    """Convert truthy or falsy value in .ini to Python boolean."""
    if x in [True, "True", "true", "1"]:
        out = True
    elif x in [False, "False", "false", "0"]:
        out = False
    elif x in [None, "None", "none"]:
        out = None
    else:
        raise ValueError(
            f"Input {x!r} is neither truthy (True, true, 1) or falsy (False, false, 0)."
        )
    return out


def reduce_node_name(node: MetaNode, paths: Sequence[str | Path]) -> str:
    """Reduce the node name.

    The whole name of the node - which includes the drive letter - can be very long
    when using nested folder structures in bigger projects.

    Thus, the part of the name which contains the path is replaced by the relative
    path from one path in ``session.config["paths"]`` to the node.

    """
    ancestor = find_closest_ancestor(node.path, paths)
    if ancestor is None:
        try:
            ancestor = find_common_ancestor(node.path, *paths)
        except ValueError:
            ancestor = node.path.parents[-1]

    if isinstance(node, MetaNode):
        name = relative_to(node.path, ancestor).as_posix()
    else:
        raise TypeError(f"Unknown node {node} with type {type(node)!r}.")

    return name


def reduce_names_of_multiple_nodes(
    names: list[str], dag: nx.DiGraph, paths: Sequence[str | Path]
) -> list[str]:
    """Reduce the names of multiple nodes in the DAG."""
    short_names = []
    for name in names:
        node = dag.nodes[name].get("node") or dag.nodes[name].get("task")

        if isinstance(node, Task):
            short_name = format_task_id(
                node, editor_url_scheme="no_link", short_name=True
            )
        elif isinstance(node, MetaNode):
            short_name = reduce_node_name(node, paths)
        else:
            raise TypeError(f"Requires 'Task' or 'MetaNode' and not {type(node)!r}.")

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
