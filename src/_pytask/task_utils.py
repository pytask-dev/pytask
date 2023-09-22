"""Contains utilities related to the ``@pytask.mark.task`` decorator."""
from __future__ import annotations

import inspect
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

import attrs
from _pytask.mark import Mark
from _pytask.models import CollectionMetadata
from _pytask.shared import find_duplicates

if TYPE_CHECKING:
    from _pytask.tree_util import PyTree


__all__ = [
    "COLLECTED_TASKS",
    "parse_collected_tasks_with_task_marker",
    "parse_keyword_arguments_from_signature_defaults",
    "task",
]


COLLECTED_TASKS: dict[Path, list[Callable[..., Any]]] = defaultdict(list)
"""A container for collecting tasks.

Tasks marked by the ``@pytask.mark.task`` decorator can be generated in a loop where one
iteration overwrites the previous task. To retrieve the tasks later, use this dictionary
mapping from paths of modules to a list of tasks per module.

"""


def task(
    name: str | None = None,
    *,
    id: str | None = None,  # noqa: A002
    kwargs: dict[Any, Any] | None = None,
    produces: PyTree[Any] = None,
) -> Callable[..., None]:
    """Decorate a task function.

    This decorator declares every callable as a pytask task.

    The function also attaches some metadata to the function like parsed kwargs and
    markers.

    Parameters
    ----------
    name
        Use it to override the name of the task that is, by default, the name of the
        callable.
    id
        An id for the task if it is part of a parametrization. Otherwise, an automatic
        id will be generated. See
        :doc:`this tutorial <../tutorials/repeating_tasks_with_different_inputs>` for
        more information.
    kwargs
        A dictionary containing keyword arguments which are passed to the task when it
        is executed.
    produces
        Definition of products to parse the function returns and store them. See
        :doc:`this how-to guide <../how_to_guides/using_task_returns>` for more
        information.

    Examples
    --------
    To mark a function without the ``task_`` prefix as a task, attach the decorator.

    .. code-block:: python

        from typing_extensions import Annotated

        @pytask.task def create_text_file() -> Annotated[str, Path("file.txt")]:
            return "Hello, World!"

    """

    def wrapper(func: Callable[..., Any]) -> None:
        for arg, arg_name in ((name, "name"), (id, "id")):
            if not (isinstance(arg, str) or arg is None):
                msg = (
                    f"Argument {arg_name!r} of @pytask.mark.task must be a str, but it "
                    f"is {arg!r}."
                )
                raise ValueError(msg)

        unwrapped = inspect.unwrap(func)

        raw_path = inspect.getfile(unwrapped)
        if "<string>" in raw_path:
            path = Path(unwrapped.__globals__["__file__"]).absolute().resolve()
        else:
            path = Path(raw_path).absolute().resolve()

        parsed_kwargs = {} if kwargs is None else kwargs
        parsed_name = name if isinstance(name, str) else func.__name__

        if hasattr(unwrapped, "pytask_meta"):
            unwrapped.pytask_meta.name = parsed_name
            unwrapped.pytask_meta.kwargs = parsed_kwargs
            unwrapped.pytask_meta.markers.append(Mark("task", (), {}))
            unwrapped.pytask_meta.id_ = id
            unwrapped.pytask_meta.produces = produces
        else:
            unwrapped.pytask_meta = CollectionMetadata(
                name=parsed_name,
                kwargs=parsed_kwargs,
                markers=[Mark("task", (), {})],
                id_=id,
                produces=produces,
            )

        # Store it in the global variable ``COLLECTED_TASKS`` to avoid garbage
        # collection when the function definition is overwritten in a loop.
        COLLECTED_TASKS[path].append(unwrapped)

        return unwrapped

    # In case the decorator is used without parentheses, wrap the function which is
    # passed as the first argument with the default arguments.
    if callable(name) and kwargs is None:
        return task()(name)
    return wrapper


def parse_collected_tasks_with_task_marker(
    tasks: list[Callable[..., Any]],
) -> dict[str, Callable[..., Any]]:
    """Parse collected tasks with a task marker."""
    parsed_tasks = _parse_tasks_with_preliminary_names(tasks)
    all_names = {i[0] for i in parsed_tasks}
    duplicated_names = find_duplicates([i[0] for i in parsed_tasks])

    collected_tasks = {}
    for name in all_names:
        if name in duplicated_names:
            selected_tasks = [i for i in parsed_tasks if i[0] == name]
            names_to_functions = _generate_ids_for_tasks(selected_tasks)
            for unique_name, task in names_to_functions.items():
                collected_tasks[unique_name] = task
        else:
            collected_tasks[name] = next(i[1] for i in parsed_tasks if i[0] == name)

    return collected_tasks


def _parse_tasks_with_preliminary_names(
    tasks: list[Callable[..., Any]],
) -> list[tuple[str, Callable[..., Any]]]:
    """Parse tasks and generate preliminary names for tasks.

    The names are preliminary since they can be duplicated and need to be extended to
    properly parametrized ids.

    """
    parsed_tasks = []
    for task in tasks:
        name, function = _parse_task(task)
        parsed_tasks.append((name, function))
    return parsed_tasks


def _parse_task(task: Callable[..., Any]) -> tuple[str, Callable[..., Any]]:
    """Parse a single task."""
    meta = task.pytask_meta  # type: ignore[attr-defined]

    if meta.name is None and task.__name__ == "_":
        msg = (
            "A task function either needs 'name' passed by the ``@pytask.mark.task`` "
            "decorator or the function name of the task function must not be '_'."
        )
        raise ValueError(msg)

    parsed_name = task.__name__ if meta.name is None else meta.name
    parsed_kwargs = _parse_task_kwargs(meta.kwargs)

    signature_kwargs = parse_keyword_arguments_from_signature_defaults(task)
    meta.kwargs = {**signature_kwargs, **parsed_kwargs}

    return parsed_name, task


def _parse_task_kwargs(kwargs: Any) -> dict[str, Any]:
    """Parse task kwargs."""
    if isinstance(kwargs, dict):
        return kwargs
    # Handle namedtuples.
    if callable(getattr(kwargs, "_asdict", None)):
        return kwargs._asdict()
    if attrs.has(type(kwargs)):
        return attrs.asdict(kwargs)
    msg = (
        "'@pytask.mark.task(kwargs=...) needs to be a dictionary, namedtuple or an "
        "instance of an attrs class."
    )
    raise ValueError(msg)


def parse_keyword_arguments_from_signature_defaults(
    task: Callable[..., Any]
) -> dict[str, Any]:
    """Parse keyword arguments from signature defaults."""
    parameters = inspect.signature(task).parameters
    kwargs = {}
    for parameter in parameters.values():
        if parameter.default is not parameter.empty:
            kwargs[parameter.name] = parameter.default
    return kwargs


def _generate_ids_for_tasks(
    tasks: list[tuple[str, Callable[..., Any]]]
) -> dict[str, Callable[..., Any]]:
    """Generate unique ids for parametrized tasks."""
    parameters = inspect.signature(tasks[0][1]).parameters

    out = {}
    for i, (name, task) in enumerate(tasks):
        if task.pytask_meta.id_ is not None:  # type: ignore[attr-defined]
            id_ = f"{name}[{task.pytask_meta.id_}]"  # type: ignore[attr-defined]
        elif not parameters:
            id_ = f"{name}[{i}]"
        else:
            stringified_args = [
                _arg_value_to_id_component(
                    arg_name=parameter,
                    arg_value=task.pytask_meta.kwargs.get(  # type: ignore[attr-defined]
                        parameter
                    ),
                    i=i,
                    id_func=None,
                )
                for parameter in parameters
            ]
            id_ = "-".join(stringified_args)
            id_ = f"{name}[{id_}]"
        out[id_] = task
    return out


def _arg_value_to_id_component(
    arg_name: str, arg_value: Any, i: int, id_func: Callable[..., Any] | None
) -> str:
    """Create id component from the name and value of the argument.

    First, transform the value of the argument with a user-defined function if given.
    Otherwise, take the original value. Then, if the value is a :obj:`bool`,
    :obj:`float`, :obj:`int`, or :obj:`str`, cast it to a string. Otherwise, define a
    placeholder value from the name of the argument and the iteration.

    Parameters
    ----------
    arg_name : str
        Name of the parametrized function argument.
    arg_value : Any
        Value of the argument.
    i : int
        The ith iteration of the parametrization.
    id_func : Union[Callable[..., Any], None]
        A callable which maps argument values to :obj:`bool`, :obj:`float`, :obj:`int`,
        or :obj:`str` or anything else. Any object with a different dtype than the first
        will be mapped to an auto-generated id component.

    Returns
    -------
    id_component : str
        A part of the final parametrized id.

    """
    id_component = id_func(arg_value) if id_func is not None else None
    if isinstance(id_component, (bool, float, int, str)):
        id_component = str(id_component)
    elif isinstance(arg_value, (bool, float, int, str)):
        id_component = str(arg_value)
    else:
        id_component = arg_name + str(i)
    return id_component
