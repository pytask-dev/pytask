"""This module contains helpers for :mod:`_pytask.collect`."""
from __future__ import annotations

import itertools
import uuid
from pathlib import Path
from typing import Any
from typing import Iterable

import attr
from _pytask.exceptions import NodeNotCollectedError
from _pytask.nodes import find_duplicates
from _pytask.nodes import MetaNode
from _pytask.session import Session


__all__ = ["convert_objects_to_node_dictionary"]


def convert_objects_to_node_dictionary(objects: Any, when: str) -> dict[Any, Any]:
    """Convert objects to node dictionary."""
    list_of_dicts = [_convert_to_dict(x) for x in objects]
    _check_that_names_are_not_used_multiple_times(list_of_dicts, when)
    nodes = _merge_dictionaries(list_of_dicts)
    return nodes


@attr.s(frozen=True)
class _Placeholder:
    """A placeholder to mark unspecified keys in dictionaries."""

    scalar = attr.ib(type=bool, default=False)
    id_ = attr.ib(factory=uuid.uuid4, type=uuid.UUID)


def _convert_to_dict(x: Any, first_level: bool = True) -> Any | dict[Any, Any]:
    """Convert any object to a dictionary."""
    if isinstance(x, dict):
        return {k: _convert_to_dict(v, False) for k, v in x.items()}
    elif isinstance(x, Iterable) and not isinstance(x, str):
        if first_level:
            return {
                _Placeholder(): _convert_to_dict(element, False)
                for i, element in enumerate(x)
            }
        else:
            return {i: _convert_to_dict(element, False) for i, element in enumerate(x)}
    elif first_level:
        return {_Placeholder(scalar=True): x}
    else:
        return x


def _collect_node(
    session: Session, path: Path, name: str, node: str | Path
) -> dict[str, MetaNode]:
    """Collect nodes for a task.

    Parameters
    ----------
    session : _pytask.session.Session
        The session.
    path : Path
        The path to the task whose nodes are collected.
    name : str
        The name of the task.
    nodes : Dict[str, Union[str, Path]]
        A dictionary of nodes parsed from the ``depends_on`` or ``produces`` markers.

    Returns
    -------
    Dict[str, MetaNode]
        A dictionary of node names and their paths.

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
            f"{node!r} cannot be parsed as a dependency or product for task "
            f"{name!r} in {path!r}."
        )

    return collected_node


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
        if placeholder.scalar:
            out = value
        else:
            out = {0: value}
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
