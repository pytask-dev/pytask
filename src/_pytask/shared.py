"""Functions which are used across various modules."""
import glob
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

import networkx as nx
from _pytask.console import escape_squared_brackets
from _pytask.nodes import create_task_name
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to


def to_list(scalar_or_iter: Any) -> List[Any]:
    """Convert scalars and iterables to list.

    Parameters
    ----------
    scalar_or_iter : str or list

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


def parse_paths(x: Optional[Any]) -> Optional[List[Path]]:
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
) -> Optional[Any]:
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
    *configs: Dict[str, Any],
    key: str,
    default: Optional[Any] = None,
    callback: Optional[Callable[..., Any]] = None,
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


def parse_value_or_multiline_option(
    value: Union[str, None]
) -> Union[None, str, List[str]]:
    """Parse option which can hold a single value or values separated by new lines."""
    if value in ["none", "None", None, ""]:
        return None
    elif isinstance(value, str) and "\n" in value:
        return [v.strip() for v in value.split("\n") if v.strip()]
    elif isinstance(value, str):
        return value.strip()
    else:
        raise ValueError(f"Input '{value}' is neither a 'str' nor 'None'.")


def convert_truthy_or_falsy_to_bool(x: Union[bool, str, None]) -> bool:
    """Convert truthy or falsy value in .ini to Python boolean."""
    if x in [True, "True", "true", "1"]:
        out = True
    elif x in [False, "False", "false", "0"]:
        out = False
    elif x in [None, "None", "none"]:
        out = None
    else:
        raise ValueError(
            f"Input '{x}' is neither truthy (True, true, 1) or falsy (False, false, 0)."
        )
    return out


def reduce_node_name(node: "MetaNode", paths: Sequence[Union[str, Path]]) -> str:
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

    if isinstance(node, MetaTask):
        shortened_path = relative_to(node.path, ancestor)
        raw_name = create_task_name(shortened_path, node.base_name)
        name = escape_squared_brackets(raw_name)
    elif isinstance(node, MetaNode):
        name = relative_to(node.path, ancestor).as_posix()
    else:
        raise TypeError(f"Unknown node {node} with type '{type(node)}'.")

    return name


def reduce_names_of_multiple_nodes(
    names: List[str], dag: nx.DiGraph, paths: Sequence[Union[str, Path]]
) -> List[str]:
    """Reduce the names of multiple nodes in the DAG."""
    return [
        reduce_node_name(dag.nodes[n].get("node") or dag.nodes[n].get("task"), paths)
        for n in names
    ]
