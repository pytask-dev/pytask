"""This module contains utilities for the database."""
from __future__ import annotations

import hashlib

from _pytask.dag_utils import node_and_neighbors
from _pytask.nodes import Task
from _pytask.session import Session
from pony import orm


__all__ = ["create_database", "db", "update_states_in_database"]


db = orm.Database()


class State(db.Entity):  # type: ignore[name-defined]
    """Represent the state of a node in relation to a task."""

    task = orm.Required(str)
    node = orm.Required(str)
    modification_time = orm.Required(str)
    file_hash = orm.Optional(str)

    orm.PrimaryKey(task, node)


def create_database(
    provider: str, filename: str, *, create_db: bool, create_tables: bool
) -> None:
    """Create the database."""
    try:
        db.bind(provider=provider, filename=filename, create_db=create_db)
        db.generate_mapping(create_tables=create_tables)
    except orm.BindingError:
        pass


@orm.db_session
def _create_or_update_state(
    first_key: str, second_key: str, modification_time: str, file_hash: str
) -> None:
    """Create or update a state."""
    try:
        state_in_db = State[first_key, second_key]  # type: ignore[type-arg, valid-type]
    except orm.ObjectNotFound:
        State(
            task=first_key,
            node=second_key,
            modification_time=modification_time,
            file_hash=file_hash,
        )
    else:
        state_in_db.modification_time = modification_time
        state_in_db.file_hash = file_hash


def update_states_in_database(session: Session, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(session.dag, task_name):
        node = session.dag.nodes[name].get("task") or session.dag.nodes[name]["node"]

        state = node.state()

        if isinstance(node, Task):
            hash_ = hashlib.sha256(node.path.read_bytes()).hexdigest()
        else:
            hash_ = ""

        _create_or_update_state(task_name, node.name, state, hash_)
