"""This module provides utility functions for :mod:`_pytask.collect`."""
from __future__ import annotations

import inspect
import itertools
import uuid
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Generator
from typing import Iterable
from typing import TYPE_CHECKING

from _pytask.exceptions import NodeNotCollectedError
from _pytask.mark_utils import remove_marks
from _pytask.nodes import ProductType
from _pytask.nodes import PythonNode
from _pytask.shared import find_duplicates
from _pytask.task_utils import parse_keyword_arguments_from_signature_defaults
from attrs import define
from attrs import field
from pybaum.tree_util import tree_map
from typing_extensions import Annotated
from typing_extensions import get_origin


if TYPE_CHECKING:
    from _pytask.session import Session
    from _pytask.nodes import MetaNode


__all__ = [
    "depends_on",
    "parse_dependencies_from_task_function",
    "parse_nodes",
    "produces",
]


def depends_on(
    objects: Any | Iterable[Any] | dict[Any, Any]
) -> Any | Iterable[Any] | dict[Any, Any]:
    """Specify dependencies for a task.

    Parameters
    ----------
    objects
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`_pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


def produces(
    objects: Any | Iterable[Any] | dict[Any, Any]
) -> Any | Iterable[Any] | dict[Any, Any]:
    """Specify products of a task.

    Parameters
    ----------
    objects
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`_pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


def parse_nodes(
    session: Session, path: Path, name: str, obj: Any, parser: Callable[..., Any]
) -> Any:
    """Parse nodes from object."""
    objects = _extract_nodes_from_function_markers(obj, parser)
    nodes = _convert_objects_to_node_dictionary(objects, parser.__name__)
    nodes = tree_map(lambda x: _collect_old_dependencies(session, path, name, x), nodes)
    return nodes


def _extract_nodes_from_function_markers(
    function: Callable[..., Any], parser: Callable[..., Any]
) -> Generator[Any, None, None]:
    """Extract nodes from a marker.

    The parser is a functions which is used to document the marker with the correct
    signature. Using the function as a parser for the ``args`` and ``kwargs`` of the
    marker provides the expected error message for misspecification.

    """
    marker_name = parser.__name__
    _, markers = remove_marks(function, marker_name)
    for marker in markers:
        parsed = parser(*marker.args, **marker.kwargs)
        yield parsed


def _convert_objects_to_node_dictionary(objects: Any, when: str) -> dict[Any, Any]:
    """Convert objects to node dictionary."""
    list_of_dicts = [_convert_to_dict(x) for x in objects]
    _check_that_names_are_not_used_multiple_times(list_of_dicts, when)
    nodes = _merge_dictionaries(list_of_dicts)
    return nodes


@define(frozen=True)
class _Placeholder:
    """A placeholder to mark unspecified keys in dictionaries."""

    scalar: bool = field(default=False)
    id_: uuid.UUID = field(factory=uuid.uuid4)


def _convert_to_dict(x: Any, first_level: bool = True) -> Any | dict[Any, Any]:
    """Convert any object to a dictionary."""
    if isinstance(x, dict):
        return {k: _convert_to_dict(v, False) for k, v in x.items()}
    if isinstance(x, Iterable) and not isinstance(x, str):
        if first_level:
            return {
                _Placeholder(): _convert_to_dict(element, False)
                for i, element in enumerate(x)
            }
        return {i: _convert_to_dict(element, False) for i, element in enumerate(x)}
    if first_level:
        return {_Placeholder(scalar=True): x}
    return x


def _check_that_names_are_not_used_multiple_times(
    list_of_dicts: list[dict[Any, Any]], when: str
) -> None:
    """Check that names of nodes are not assigned multiple times.

    Tuples in the list have either one or two elements. The first element in the two
    element tuples is the name and cannot occur twice.

    """
    names_with_provisional_keys = list(
        itertools.chain.from_iterable(dict_.keys() for dict_ in list_of_dicts)
    )
    names = [x for x in names_with_provisional_keys if not isinstance(x, _Placeholder)]
    duplicated = find_duplicates(names)

    if duplicated:
        raise ValueError(
            f"'@pytask.mark.{when}' has nodes with the same name: {duplicated}"
        )


def _union_of_dictionaries(dicts: list[dict[Any, Any]]) -> dict[Any, Any]:
    """Merge multiple dictionaries in one.

    Examples
    --------
    >>> a, b = {"a": 0}, {"b": 1}
    >>> _union_of_dictionaries([a, b])
    {'a': 0, 'b': 1}

    >>> a, b = {'a': 0}, {'a': 1}
    >>> _union_of_dictionaries([a, b])
    {'a': 1}

    """
    return dict(itertools.chain.from_iterable(dict_.items() for dict_ in dicts))


def _merge_dictionaries(list_of_dicts: list[dict[Any, Any]]) -> dict[Any, Any]:
    """Merge multiple dictionaries.

    The function does not perform a deep merge. It simply merges the dictionary based on
    the first level keys which are either unique names or placeholders. During the merge
    placeholders will be replaced by an incrementing integer.

    Examples
    --------
    >>> a, b = {"a": 0}, {"b": 1}
    >>> _merge_dictionaries([a, b])
    {'a': 0, 'b': 1}

    >>> a, b = {_Placeholder(): 0}, {_Placeholder(): 1}
    >>> _merge_dictionaries([a, b])
    {0: 0, 1: 1}

    """
    merged_dict = _union_of_dictionaries(list_of_dicts)

    if len(merged_dict) == 1 and isinstance(list(merged_dict)[0], _Placeholder):
        placeholder, value = list(merged_dict.items())[0]
        out = value if placeholder.scalar else {0: value}
    else:
        counter = itertools.count()
        out = {}
        for k, v in merged_dict.items():
            if isinstance(k, _Placeholder):
                while True:
                    possible_key = next(counter)
                    if possible_key not in merged_dict and possible_key not in out:
                        out[possible_key] = v
                        break
            else:
                out[k] = v

    return out


def parse_dependencies_from_task_function(
    session: Session, path: Path, name: str, obj: Any
) -> dict[str, Any]:
    """Parse dependencies from task function."""
    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    signature_defaults = parse_keyword_arguments_from_signature_defaults(obj)
    kwargs = {**signature_defaults, **task_kwargs}
    kwargs.pop("produces", None)

    parameters_with_product_annot = _find_args_with_product_annotation(obj)

    dependencies = {}
    for name, value in kwargs.items():
        if name in parameters_with_product_annot:
            continue
        parsed_value = tree_map(
            lambda x: _collect_dependencies(session, path, name, x), value  # noqa: B023
        )
        dependencies[name] = (
            PythonNode(value=None) if parsed_value is None else parsed_value
        )

    return dependencies


def parse_products_from_task_function(
    session: Session, path: Path, name: str, obj: Any
) -> dict[str, Any]:
    """Parse products from task function."""
    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    if "produces" in task_kwargs:
        collected_products = tree_map(
            lambda x: _collect_product(session, path, name, x, is_string_allowed=True),
            task_kwargs["produces"],
        )
        return {"produces": collected_products}

    parameters = inspect.signature(obj).parameters
    if "produces" in parameters:
        parameter = parameters["produces"]
        if parameter.default is not parameter.empty:
            # Use _collect_new_node to not collect strings.
            collected_products = tree_map(
                lambda x: _collect_product(
                    session, path, name, x, is_string_allowed=False
                ),
                parameter.default,
            )
            return {"produces": collected_products}

    parameters_with_product_annot = _find_args_with_product_annotation(obj)
    if parameters_with_product_annot:
        for parameter_name in parameters_with_product_annot:
            parameter = parameters[parameter_name]
            if parameter.default is not parameter.empty:
                # Use _collect_new_node to not collect strings.
                collected_products = tree_map(
                    lambda x: _collect_product(
                        session, path, name, x, is_string_allowed=False
                    ),
                    parameter.default,
                )
                return {parameter_name: collected_products}
    return {}


def _find_args_with_product_annotation(func: Callable[..., Any]) -> list[str]:
    """Find args with product annotation."""
    annotations = inspect.get_annotations(func, eval_str=True)
    metas = {
        name: annotation.__metadata__
        for name, annotation in annotations.items()
        if get_origin(annotation) is Annotated
    }

    args_with_product_annot = []
    for name, meta in metas.items():
        has_product_annot = any(isinstance(i, ProductType) for i in meta)
        if has_product_annot:
            args_with_product_annot.append(name)

    return args_with_product_annot


def _collect_old_dependencies(
    session: Session, path: Path, name: str, node: str | Path
) -> dict[str, MetaNode]:
    """Collect nodes for a task.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    if not isinstance(node, (str, Path)):
        raise ValueError(
            "'@pytask.mark.depends_on' and '@pytask.mark.produces' can only accept "
            "values of type 'str' and 'pathlib.Path' or the same values nested in "
            f"tuples, lists, and dictionaries. Here, {node} has type {type(node)}."
        )

    if isinstance(node, str):
        node = Path(node)

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node=node
    )
    if collected_node is None:
        raise NodeNotCollectedError(
            f"{node!r} cannot be parsed as a dependency or product for task "
            f"{name!r} in {path!r}."
        )

    return collected_node


def _collect_dependencies(
    session: Session, path: Path, name: str, node: Any
) -> dict[str, MetaNode]:
    """Collect nodes for a task.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node=node
    )
    if collected_node is None:
        raise NodeNotCollectedError(
            f"{node!r} cannot be parsed as a dependency for task "
            f"{name!r} in {path!r}."
        )
    return collected_node


def _collect_product(
    session: Session,
    path: Path,
    name: str,
    node: str | Path,
    is_string_allowed: bool = False,
) -> dict[str, MetaNode]:
    """Collect products for a task.

    Defining products with strings is only allowed when using the decorator. Parameter
    defaults can only be :class:`pathlib.Path`s.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    # For historical reasons, task.kwargs is like the deco and supports str and Path.
    if not isinstance(node, (str, Path)) and is_string_allowed:
        raise ValueError(
            "`@pytask.mark.task(kwargs={'produces': ...}` can only accept values of "
            "type 'str' and 'pathlib.Path' or the same values nested in "
            f"tuples, lists, and dictionaries. Here, {node} has type {type(node)}."
        )
    # The parameter defaults only support Path objects.
    if not isinstance(node, Path) and not is_string_allowed:
        raise ValueError(
            "If you use 'produces' as an argument of a task, it can only accept values "
            "of type 'pathlib.Path' or the same value nested in "
            f"tuples, lists, and dictionaries. Here, {node} has type {type(node)}."
        )

    if isinstance(node, str):
        node = Path(node)

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node=node
    )
    if collected_node is None:
        raise NodeNotCollectedError(
            f"{node!r} cannot be parsed as a dependency or product for task "
            f"{name!r} in {path!r}."
        )

    return collected_node
