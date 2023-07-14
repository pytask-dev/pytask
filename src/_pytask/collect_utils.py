"""This module provides utility functions for :mod:`_pytask.collect`."""
from __future__ import annotations

import itertools
import uuid
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Generator
from typing import Iterable
from typing import TYPE_CHECKING

import attrs
from _pytask._inspect import get_annotations
from _pytask.exceptions import NodeNotCollectedError
from _pytask.mark_utils import has_mark
from _pytask.mark_utils import remove_marks
from _pytask.models import NodeInfo
from _pytask.nodes import MetaNode
from _pytask.nodes import ProductType
from _pytask.nodes import PythonNode
from _pytask.shared import find_duplicates
from _pytask.task_utils import parse_keyword_arguments_from_signature_defaults
from _pytask.tree_util import tree_leaves
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_map_with_path
from attrs import define
from attrs import field
from typing_extensions import Annotated
from typing_extensions import get_origin


if TYPE_CHECKING:
    from _pytask.session import Session


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
    arg_name = parser.__name__
    objects = _extract_nodes_from_function_markers(obj, parser)
    nodes = _convert_objects_to_node_dictionary(objects, arg_name)
    nodes = tree_map(
        lambda x: _collect_decorator_nodes(
            session, path, name, NodeInfo(arg_name, (), x)
        ),
        nodes,
    )
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


_ERROR_MULTIPLE_DEPENDENCY_DEFINITIONS = """"Dependencies are defined via \
'@pytask.mark.depends_on' and as default arguments for the argument 'depends_on'. Use \
only one way and not both.

Hint: You do not need to use 'depends_on' since pytask v0.4. Every function argument \
that is not a product is treated as a dependency. Read more about dependencies in the \
documentation: https://tinyurl.com/yrezszr4.
"""


def parse_dependencies_from_task_function(  # noqa: C901
    session: Session, path: Path, name: str, obj: Any
) -> dict[str, Any]:
    """Parse dependencies from task function."""
    has_depends_on_decorator = False
    has_depends_on_argument = False

    if has_mark(obj, "depends_on"):
        nodes = parse_nodes(session, path, name, obj, depends_on)
        return {"depends_on": nodes}

    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    signature_defaults = parse_keyword_arguments_from_signature_defaults(obj)
    kwargs = {**signature_defaults, **task_kwargs}
    kwargs.pop("produces", None)

    dependencies = {}
    # Parse products from task decorated with @task and that uses produces.
    if "depends_on" in kwargs:
        has_depends_on_argument = True
        dependencies["depends_on"] = tree_map(
            lambda x: _collect_decorator_nodes(
                session, path, name, NodeInfo(arg_name="depends_on", path=(), value=x)
            ),
            kwargs["depends_on"],
        )

    if has_depends_on_decorator and has_depends_on_argument:
        raise NodeNotCollectedError(_ERROR_MULTIPLE_PRODUCT_DEFINITIONS)

    parameters_with_product_annot = _find_args_with_product_annotation(obj)
    parameters_with_node_annot = _find_args_with_node_annotation(obj)

    for parameter_name, value in kwargs.items():
        if parameter_name in parameters_with_product_annot:
            continue

        if parameter_name == "depends_on":
            continue

        if parameter_name in parameters_with_node_annot:

            def _evolve(x: Any) -> Any:
                instance = parameters_with_node_annot[parameter_name]  # noqa: B023
                return attrs.evolve(instance, value=x)  # type: ignore[misc]

        else:

            def _evolve(x: Any) -> Any:
                return x

        nodes = tree_map_with_path(
            lambda p, x: _collect_dependencies(
                session,
                path,
                name,
                NodeInfo(parameter_name, p, _evolve(x)),  # noqa: B023
            ),
            value,
        )

        # If all nodes are python nodes, we simplify the parameter value and store it in
        # one node.
        are_all_nodes_python_nodes_without_hash = all(
            isinstance(x, PythonNode) and not x.hash for x in tree_leaves(nodes)
        )
        if are_all_nodes_python_nodes_without_hash:
            dependencies[parameter_name] = PythonNode(value=value, name=parameter_name)
        else:
            dependencies[parameter_name] = nodes
    return dependencies


def _find_args_with_node_annotation(func: Callable[..., Any]) -> dict[str, MetaNode]:
    """Find args with node annotations."""
    annotations = get_annotations(func, eval_str=True)
    metas = {
        name: annotation.__metadata__
        for name, annotation in annotations.items()
        if get_origin(annotation) is Annotated
    }

    args_with_node_annotation = {}
    for name, meta in metas.items():
        annot = [
            i
            for i in meta
            if not isinstance(i, ProductType) and isinstance(i, MetaNode)
        ]
        if len(annot) >= 2:  # noqa: PLR2004
            raise ValueError(
                f"Parameter {name!r} has multiple node annotations although only one "
                f"is allowed. Annotations: {annot}"
            )
        if annot:
            args_with_node_annotation[name] = annot[0]

    return args_with_node_annotation


_ERROR_MULTIPLE_PRODUCT_DEFINITIONS = """The task uses multiple ways to define \
products. Products should be defined with either

- 'typing.Annotated[Path(...), Product]' (recommended)
- '@pytask.mark.task(kwargs={'produces': Path(...)})'
- as a default argument for 'produces': 'produces = Path(...)'
- '@pytask.mark.produces(Path(...))' (deprecated)

Read more about products in the documentation: https://tinyurl.com/yrezszr4.
"""


def parse_products_from_task_function(
    session: Session, path: Path, name: str, obj: Any
) -> dict[str, Any]:
    """Parse products from task function.

    Raises
    ------
    NodeNotCollectedError
        If multiple ways were used to specify products.

    """
    has_produces_decorator = False
    has_produces_argument = False
    has_annotation = False
    out = {}

    # Parse products from decorators.
    if has_mark(obj, "produces"):
        has_produces_decorator = True
        nodes = parse_nodes(session, path, name, obj, produces)
        out = {"produces": nodes}

    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    signature_defaults = parse_keyword_arguments_from_signature_defaults(obj)
    kwargs = {**signature_defaults, **task_kwargs}

    # Parse products from task decorated with @task and that uses produces.
    if "produces" in kwargs:
        has_produces_argument = True
        collected_products = tree_map_with_path(
            lambda p, x: _collect_product(
                session,
                path,
                name,
                NodeInfo(arg_name="produces", path=p, value=x),
                is_string_allowed=True,
            ),
            kwargs["produces"],
        )
        out = {"produces": collected_products}

    parameters_with_product_annot = _find_args_with_product_annotation(obj)
    if parameters_with_product_annot:
        has_annotation = True
        for parameter_name in parameters_with_product_annot:
            if parameter_name in kwargs:
                # Use _collect_new_node to not collect strings.
                collected_products = tree_map_with_path(
                    lambda p, x: _collect_product(
                        session,
                        path,
                        name,
                        NodeInfo(parameter_name, p, x),  # noqa: B023
                        is_string_allowed=False,
                    ),
                    kwargs[parameter_name],
                )
                out = {parameter_name: collected_products}

    if (
        sum((has_produces_decorator, has_produces_argument, has_annotation))
        >= 2  # noqa: PLR2004
    ):
        raise NodeNotCollectedError(_ERROR_MULTIPLE_PRODUCT_DEFINITIONS)

    return out


def _find_args_with_product_annotation(func: Callable[..., Any]) -> list[str]:
    """Find args with product annotations."""
    annotations = get_annotations(func, eval_str=True)
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


_ERROR_WRONG_TYPE_DECORATOR = """'@pytask.mark.depends_on', '@pytask.mark.produces', \
and their function arguments can only accept values of type 'str' and 'pathlib.Path' \
or the same values nested in tuples, lists, and dictionaries. Here, {node} has type \
{node_type}.
"""


def _collect_decorator_nodes(
    session: Session, path: Path, name: str, node_info: NodeInfo
) -> dict[str, MetaNode]:
    """Collect nodes for a task.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    node = node_info.value

    if not isinstance(node, (str, Path)):
        raise NodeNotCollectedError(
            _ERROR_WRONG_TYPE_DECORATOR.format(node=node, node_type=type(node))
        )

    if isinstance(node, str):
        node = Path(node)
        node_info = node_info._replace(value=node)

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node_info=node_info
    )
    if collected_node is None:
        kind = {"depends_on": "dependency", "produces": "product"}.get(
            node_info.arg_name
        )
        raise NodeNotCollectedError(
            f"{node!r} cannot be parsed as a {kind} for task {name!r} in {path!r}."
        )

    return collected_node


def _collect_dependencies(
    session: Session, path: Path, name: str, node_info: NodeInfo
) -> dict[str, MetaNode]:
    """Collect nodes for a task.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    node = node_info.value

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node_info=node_info
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
    task_name: str,
    node_info: NodeInfo,
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
    node = node_info.value
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
            "If you use 'produces' as a function argument of a task and pass values as "
            "function defaults, it can only accept values of type 'pathlib.Path' or "
            "the same value nested in tuples, lists, and dictionaries. Here, "
            f"{node!r} has type {type(node)}."
        )

    if isinstance(node, str):
        node = Path(node)
        node_info = node_info._replace(value=node)

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node_info=node_info
    )
    if collected_node is None:
        raise NodeNotCollectedError(
            f"{node!r} can't be parsed as a product for task {task_name!r} in {path!r}."
        )

    return collected_node
