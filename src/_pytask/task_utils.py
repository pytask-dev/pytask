"""This module contains utilities related to the ``@pytask.mark.task`` decorator."""
from __future__ import annotations

import inspect
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Callable

from _pytask.mark import Mark
from _pytask.models import CollectionMetadata
from _pytask.parametrize_utils import arg_value_to_id_component
from _pytask.shared import find_duplicates


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
) -> Callable[..., None]:
    """Parse inputs of the ``@pytask.mark.task`` decorator.

    The decorator wraps task functions and stores it in the global variable
    :obj:`COLLECTED_TASKS` to avoid garbage collection when the function definition is
    overwritten in a loop.

    The function also attaches some metadata to the function like parsed kwargs and
    markers.

    Parameters
    ----------
    name : str | None
        The name of the task.
    id : str | None
        An id for the task if it is part of a parametrization.
    kwargs : dict[Any, Any] | None
        A dictionary containing keyword arguments which are passed to the task when it
        is executed.

    """

    def wrapper(func: Callable[..., Any]) -> None:
        unwrapped = inspect.unwrap(func)
        path = Path(inspect.getfile(unwrapped)).absolute().resolve()
        parsed_kwargs = {} if kwargs is None else kwargs
        parsed_name = name if isinstance(name, str) else func.__name__

        if hasattr(unwrapped, "pytask_meta"):
            unwrapped.pytask_meta.name = parsed_name
            unwrapped.pytask_meta.kwargs = parsed_kwargs
            unwrapped.pytask_meta.markers.append(Mark("task", (), {}))
            unwrapped.pytask_meta.id_ = id
        else:
            unwrapped.pytask_meta = CollectionMetadata(
                name=parsed_name,
                kwargs=parsed_kwargs,
                markers=[Mark("task", (), {})],
                id_=id,
            )

        COLLECTED_TASKS[path].append(unwrapped)

        return unwrapped

    # In case the decorator is used without parentheses, wrap the function which is
    # passed as the first argument with the default arguments.
    if callable(name) and kwargs is None:
        return task()(name)
    else:
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
            collected_tasks[name] = [i[1] for i in parsed_tasks if i[0] == name][0]

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
    name = task.pytask_meta.name  # type: ignore[attr-defined]
    if name is None and task.__name__ == "_":
        raise ValueError(
            "A task function either needs 'name' passed by the ``@pytask.mark.task`` "
            "decorator or the function name of the task function must not be '_'."
        )
    else:
        parsed_name = task.__name__ if name is None else name

    signature_kwargs = _parse_keyword_arguments_from_signature_defaults(task)
    task.pytask_meta.kwargs = {  # type: ignore[attr-defined]
        **task.pytask_meta.kwargs,  # type: ignore[attr-defined]
        **signature_kwargs,
    }

    return parsed_name, task


def _parse_keyword_arguments_from_signature_defaults(
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
            id_ = f"{name}[{str(task.pytask_meta.id_)}]"  # type: ignore[attr-defined]
        elif not parameters:
            id_ = f"{name}[{i}]"
        else:
            stringified_args = [
                arg_value_to_id_component(
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
