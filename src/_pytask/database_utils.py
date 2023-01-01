"""This module contains utilities for the database."""
from __future__ import annotations

import networkx as nx
from _pytask.dag import node_and_neighbors
from pony import orm


__all__ = ["create_database", "db", "update_states_in_database"]


db = orm.Database()


class State(db.Entity):  # type: ignore
    """Represent the state of a node in relation to a task."""

    task = orm.Required(str)
    node = orm.Required(str)
    state = orm.Required(str)

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
def _create_or_update_state(first_key: str, second_key: str, state: str) -> None:
    """Create or update a state."""
    try:
        state_in_db = State[first_key, second_key]  # type: ignore
    except orm.ObjectNotFound:
        State(task=first_key, node=second_key, state=state)
    else:
        state_in_db.state = state


def update_states_in_database(dag: nx.DiGraph, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        _create_or_update_state(task_name, node.name, node.state())
