"""Contains utility functions for :mod:`_pytask.collect`."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any
from typing import Callable
from typing import get_origin

import attrs

from _pytask._inspect import get_annotations
from _pytask.exceptions import NodeNotCollectedError
from _pytask.models import NodeInfo
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.nodes import PythonNode
from _pytask.task_utils import parse_keyword_arguments_from_signature_defaults
from _pytask.tree_util import PyTree
from _pytask.tree_util import tree_leaves
from _pytask.tree_util import tree_map_with_path
from _pytask.typing import ProductType
from _pytask.typing import no_default

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.session import Session


__all__ = [
    "collect_dependency",
    "parse_dependencies_from_task_function",
    "parse_products_from_task_function",
]


_ERROR_MULTIPLE_DEPENDENCY_DEFINITIONS = """The task uses multiple ways to define \
dependencies. Dependencies should be defined with either

- as default value for the function argument 'depends_on'.
- as '@pytask.task(kwargs={"depends_on": ...})'

Use only one of the two ways!

Hint: You do not need to use 'depends_on' as the argument name since pytask v0.4. \
Every function argument that is not a product is treated as a dependency. Read more \
about dependencies in the documentation: https://tinyurl.com/pytask-deps-prods.
"""


def parse_dependencies_from_task_function(
    session: Session, task_path: Path | None, task_name: str, node_path: Path, obj: Any
) -> dict[str, Any]:
    """Parse dependencies from task function."""
    dependencies = {}

    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    signature_defaults = parse_keyword_arguments_from_signature_defaults(obj)
    kwargs = {**signature_defaults, **task_kwargs}
    kwargs.pop("produces", None)

    parameters_with_product_annot = _find_args_with_product_annotation(obj)
    parameters_with_product_annot.append("return")
    parameters_with_node_annot = _find_args_with_node_annotation(obj)

    # Complete kwargs with node annotations, when no value is given by kwargs.
    for name in list(parameters_with_node_annot):
        if name not in kwargs:
            kwargs[name] = parameters_with_node_annot.pop(name)
        else:
            msg = (
                f"The value for the parameter {name!r} is defined twice, in "
                "'@task(kwargs=...)' and in the type annotation. Choose only one way."
            )
            raise ValueError(msg)

    for parameter_name, value in kwargs.items():
        if parameter_name in parameters_with_product_annot:
            continue

        nodes = _collect_nodes_and_provisional_nodes(
            collect_dependency,
            session,
            node_path,
            task_name,
            task_path,
            parameter_name,
            value,
        )

        # If all nodes are python nodes, we simplify the parameter value and store it in
        # one node. If it is a node, we keep it.
        are_all_nodes_python_nodes_without_hash = all(
            isinstance(x, PythonNode) and not x.hash for x in tree_leaves(nodes)
        )
        if (
            not isinstance(nodes, (PNode, PProvisionalNode))
            and are_all_nodes_python_nodes_without_hash
        ):
            node_name = create_name_of_python_node(
                NodeInfo(
                    arg_name=parameter_name,
                    path=(),
                    value=value,
                    task_path=task_path,
                    task_name=task_name,
                )
            )
            dependencies[parameter_name] = PythonNode(value=value, name=node_name)
        else:
            dependencies[parameter_name] = nodes  # type: ignore[assignment]
    return dependencies


def _find_args_with_node_annotation(
    func: Callable[..., Any],
) -> dict[str, PNode | PProvisionalNode]:
    """Find args with node annotations."""
    annotations = get_annotations(func, eval_str=True)
    metas = {
        name: annotation.__metadata__
        for name, annotation in annotations.items()
        if get_origin(annotation) is Annotated
    }

    args_with_node_annotation = {}
    for name, meta in metas.items():
        annot = [i for i in meta if not isinstance(i, ProductType)]
        if len(annot) >= 2:  # noqa: PLR2004
            msg = (
                f"Parameter {name!r} has multiple node annotations although only one "
                f"is allowed. Annotations: {annot}"
            )
            raise ValueError(msg)
        if annot:
            args_with_node_annotation[name] = annot[0]

    return args_with_node_annotation


_ERROR_MULTIPLE_TASK_RETURN_DEFINITIONS = """The task uses multiple ways to parse \
products from the return of the task function. Use either

def task_example() -> Annotated[str, Path("file.txt")]:
    ...

or

@task(produces=Path("file.txt"))
def task_example() -> str:
    ...

Read more about products in the documentation: http://tinyurl.com/pytask-return.
"""


def parse_products_from_task_function(
    session: Session, task_path: Path | None, task_name: str, node_path: Path, obj: Any
) -> dict[str, Any]:
    """Parse products from task function.

    Raises
    ------
    NodeNotCollectedError
        If multiple ways to parse products from the return of the task function are
        used.

    """
    has_return = False
    has_task_decorator = False

    out: dict[str, Any] = {}

    task_kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}
    signature_defaults = parse_keyword_arguments_from_signature_defaults(obj)
    kwargs = {**signature_defaults, **task_kwargs}

    parameters = list(inspect.signature(obj).parameters)
    parameters_with_product_annot = _find_args_with_product_annotation(obj)
    parameters_with_node_annot = _find_args_with_node_annotation(obj)

    # Allow to collect products from 'produces'.
    if "produces" in parameters and "produces" not in parameters_with_product_annot:
        parameters_with_product_annot.append("produces")

    if "return" in parameters_with_node_annot:
        parameters_with_product_annot.append("return")
        has_return = True

    if parameters_with_product_annot:
        out = {}
        for parameter_name in parameters_with_product_annot:
            # Makes sure that missing products will show up as missing inputs during the
            # execution.
            if (
                parameter_name not in kwargs
                and parameter_name not in parameters_with_node_annot
            ):
                continue

            if (
                parameter_name in kwargs
                and parameter_name in parameters_with_node_annot
            ):
                msg = (
                    f"The value for the parameter {parameter_name!r} is defined twice, "
                    "in '@task(kwargs=...)' and in the type annotation. Choose only "
                    "one way."
                )
                raise ValueError(msg)

            value = kwargs.get(parameter_name) or parameters_with_node_annot.get(
                parameter_name
            )
            collected_products = _collect_nodes_and_provisional_nodes(
                _collect_product,
                session,
                node_path,
                task_name,
                task_path,
                parameter_name,
                value,
            )
            out[parameter_name] = collected_products

    task_produces = obj.pytask_meta.produces if hasattr(obj, "pytask_meta") else None
    if task_produces:
        has_task_decorator = True
        collected_products = _collect_nodes_and_provisional_nodes(
            _collect_product,
            session,
            node_path,
            task_name,
            task_path,
            "return",
            task_produces,
        )
        out = {"return": collected_products}

    if sum((has_return, has_task_decorator)) == 2:  # noqa: PLR2004
        raise NodeNotCollectedError(_ERROR_MULTIPLE_TASK_RETURN_DEFINITIONS)

    return out


def _collect_nodes_and_provisional_nodes(  # noqa: PLR0913
    collection_func: Callable[..., Any],
    session: Session,
    node_path: Path,
    task_name: str,
    task_path: Path | None,
    parameter_name: str,
    value: Any,
) -> PyTree[PProvisionalNode | PNode]:
    return tree_map_with_path(
        lambda p, x: collection_func(
            session,
            node_path,
            task_name,
            NodeInfo(
                arg_name=parameter_name,
                path=p,
                value=x,
                task_path=task_path,
                task_name=task_name,
            ),
        ),
        value,
    )


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


def collect_dependency(
    session: Session, path: Path, name: str, node_info: NodeInfo
) -> PNode | PProvisionalNode:
    """Collect nodes for a task.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    node = node_info.value

    if isinstance(node, PythonNode) and node.value is no_default:
        # If a node is a dependency and its value is not set, the node is a product in
        # another task and the value will be set there. Thus, we wrap the original node
        # in another node to retrieve the value after it is set.
        new_node = attrs.evolve(node, value=node)
        node_info = node_info._replace(value=new_node)

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node_info=node_info
    )
    if collected_node is None:  # pragma: no cover
        msg = (
            f"{node!r} cannot be parsed as a dependency for task {name!r} in {path!r}."
        )
        raise NodeNotCollectedError(msg)
    return collected_node


def _collect_product(
    session: Session,
    path: Path,
    task_name: str,
    node_info: NodeInfo,
) -> PNode | PProvisionalNode:
    """Collect products for a task.

    Defining products with strings is only allowed when using the decorator. Parameter
    defaults can only be :class:`pathlib.Path`s.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    node = node_info.value

    collected_node = session.hook.pytask_collect_node(
        session=session, path=path, node_info=node_info
    )

    if collected_node is None:  # pragma: no cover
        msg = (
            f"{node!r} can't be parsed as a product for task {task_name!r} in {path!r}."
        )
        raise NodeNotCollectedError(msg)

    return collected_node


def create_name_of_python_node(node_info: NodeInfo) -> str:
    """Create name of PythonNode."""
    prefix = node_info.task_name if node_info.task_path else node_info.task_name
    node_name = prefix + "::" + node_info.arg_name
    if node_info.path:
        suffix = "-".join(map(str, node_info.path))
        node_name += "::" + suffix
    return node_name
