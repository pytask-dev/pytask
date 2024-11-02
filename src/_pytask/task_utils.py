"""Contains utilities related to the :func:`@task <pytask.task>`."""

from __future__ import annotations

import functools
import inspect
from collections import defaultdict
from types import BuiltinFunctionType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

import attrs

from _pytask.coiled_utils import Function
from _pytask.coiled_utils import extract_coiled_function_kwargs
from _pytask.console import get_file
from _pytask.mark import Mark
from _pytask.models import CollectionMetadata
from _pytask.shared import find_duplicates
from _pytask.shared import unwrap_task_function
from _pytask.typing import is_task_function

if TYPE_CHECKING:
    from pathlib import Path


__all__ = [
    "COLLECTED_TASKS",
    "parse_collected_tasks_with_task_marker",
    "parse_keyword_arguments_from_signature_defaults",
    "task",
]


COLLECTED_TASKS: dict[Path | None, list[Callable[..., Any]]] = defaultdict(list)
"""A container for collecting tasks.

Tasks marked by the :func:`@task <pytask.task>` decorator can be generated in a loop
where one iteration overwrites the previous task. To retrieve the tasks later, use this
dictionary mapping from paths of modules to a list of tasks per module.

"""


def task(  # noqa: PLR0913
    name: str | None = None,
    *,
    after: str | Callable[..., Any] | list[Callable[..., Any]] | None = None,
    is_generator: bool = False,
    id: str | None = None,  # noqa: A002
    kwargs: dict[Any, Any] | None = None,
    produces: Any | None = None,
) -> Callable[..., Callable[..., Any]]:
    """Decorate a task function.

    This decorator declares every callable as a pytask task.

    The function also attaches some metadata to the function like parsed kwargs and
    markers.

    Parameters
    ----------
    name
        Use it to override the name of the task that is, by default, the name of the
        task function. Read :ref:`customize-task-names` for more information.
    after
        An expression or a task function or a list of task functions that need to be
        executed before this task can be executed. See :ref:`after` for more
        information.
    is_generator
        An indicator whether this task is a task generator.
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
    id
        An id for the task if it is part of a repetition. Otherwise, an automatic id
        will be generated. See :ref:`how-to-repeat-a-task-with-different-inputs-the-id`
        for more information.
    kwargs
        Use a dictionary to pass any keyword arguments to the task function which can be
        dependencies or products of the task. Read :ref:`task-kwargs` for more
        information.
    produces
        Use this argument if you want to parse the return of the task function as a
        product, but you cannot annotate the return of the function. See :doc:`this
        how-to guide <../how_to_guides/using_task_returns>` or :ref:`task-produces` for
        more information.

    Examples
    --------
    To mark a function without the ``task_`` prefix as a task, attach the decorator.

    .. code-block:: python

        from typing import Annotated from pytask import task

        @task()
        def create_text_file() -> Annotated[str, Path("file.txt")]:
            return "Hello, World!"

    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        # Omits frame when a builtin function is wrapped.
        _rich_traceback_omit = True

        for arg, arg_name in ((name, "name"), (id, "id")):
            if not (isinstance(arg, str) or arg is None):
                msg = (
                    f"Argument {arg_name!r} of @task must be a str, but it is {arg!r}."
                )
                raise ValueError(msg)

        unwrapped = unwrap_task_function(func)
        if isinstance(unwrapped, Function):
            coiled_kwargs = extract_coiled_function_kwargs(unwrapped)
            unwrapped = unwrap_task_function(unwrapped.function)
        else:
            coiled_kwargs = None

        # We do not allow builtins as functions because we would need to use
        # ``inspect.stack`` to infer their caller location and they are unable to carry
        # the pytask metadata.
        if isinstance(unwrapped, BuiltinFunctionType):
            msg = (
                "Builtin functions cannot be wrapped with '@task'. If necessary, wrap "
                "the builtin function in a function or lambda expression."
            )
            raise NotImplementedError(msg)

        path = get_file(unwrapped)

        parsed_kwargs = {} if kwargs is None else kwargs
        parsed_name = _parse_name(unwrapped, name)
        parsed_after = _parse_after(after)

        if hasattr(unwrapped, "pytask_meta"):
            unwrapped.pytask_meta.after = parsed_after
            unwrapped.pytask_meta.is_generator = is_generator
            unwrapped.pytask_meta.id_ = id
            unwrapped.pytask_meta.kwargs = parsed_kwargs
            unwrapped.pytask_meta.markers.append(Mark("task", (), {}))
            unwrapped.pytask_meta.name = parsed_name
            unwrapped.pytask_meta.produces = produces
            unwrapped.pytask_meta.after = parsed_after
        else:
            unwrapped.pytask_meta = CollectionMetadata(  # type: ignore[attr-defined]
                after=parsed_after,
                is_generator=is_generator,
                id_=id,
                kwargs=parsed_kwargs,
                markers=[Mark("task", (), {})],
                name=parsed_name,
                produces=produces,
            )

        if coiled_kwargs and hasattr(unwrapped, "pytask_meta"):
            unwrapped.pytask_meta.attributes["coiled_kwargs"] = coiled_kwargs

        # Store it in the global variable ``COLLECTED_TASKS`` to avoid garbage
        # collection when the function definition is overwritten in a loop.
        COLLECTED_TASKS[path].append(unwrapped)

        return unwrapped

    # In case the decorator is used without parentheses, wrap the function which is
    # passed as the first argument with the default arguments.
    if is_task_function(name) and kwargs is None:
        return task()(name)
    return wrapper


def _parse_name(func: Callable[..., Any], name: str | None) -> str:
    """Parse name from task function."""
    if name:
        return name

    if isinstance(func, functools.partial):
        func = func.func

    if hasattr(func, "__name__"):
        return func.__name__

    msg = "Cannot infer name for task function."
    raise NotImplementedError(msg)


def _parse_after(
    after: str | Callable[..., Any] | list[Callable[..., Any]] | None,
) -> str | list[Callable[..., Any]]:
    if not after:
        return []
    if isinstance(after, str):
        return after
    if callable(after):
        after = [after]
    if isinstance(after, list):
        new_after = []
        for func in after:
            if not hasattr(func, "pytask_meta"):
                func = task()(func)  # noqa: PLW2901
            new_after.append(func.pytask_meta._id)
        return new_after
    msg = (
        "'after' should be an expression string, a task, or a list of tasks. Got "
        f"{after}, instead."
    )
    raise TypeError(msg)


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
            collected_tasks.update(names_to_functions)
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
            "A task function either needs 'name' passed by the ``@task`` "
            "decorator or the function name of the task function must not be '_'."
        )
        raise ValueError(msg)

    parsed_name = task.__name__ if meta.name is None else meta.name
    parsed_kwargs = _parse_task_kwargs(meta.kwargs)

    signature_kwargs = parse_keyword_arguments_from_signature_defaults(task)
    meta.kwargs = signature_kwargs | parsed_kwargs

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
        "'@task(kwargs=...) needs to be a dictionary, namedtuple or an "
        "instance of an attrs class."
    )
    raise ValueError(msg)


def parse_keyword_arguments_from_signature_defaults(
    task: Callable[..., Any],
) -> dict[str, Any]:
    """Parse keyword arguments from signature defaults."""
    parameters = inspect.signature(task).parameters
    kwargs = {}
    for parameter in parameters.values():
        if parameter.default is not parameter.empty:
            kwargs[parameter.name] = parameter.default
    return kwargs


def _generate_ids_for_tasks(
    tasks: list[tuple[str, Callable[..., Any]]],
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

        if id_ in out:
            msg = (
                f"The task {name!r} with the id {id_!r} is duplicated. This can happen "
                "if you create the exact same tasks multiple times or passed the same "
                "the same id to multiple tasks via '@task(id=...)'."
            )
            raise ValueError(msg)
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
