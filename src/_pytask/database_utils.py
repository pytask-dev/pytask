"""Contains utilities for the database."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker

from _pytask.dag_utils import node_and_neighbors

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PTask
    from _pytask.session import Session


__all__ = [
    "BaseTable",
    "DatabaseSession",
    "create_database",
    "update_states_in_database",
]


DatabaseSession = sessionmaker()


class BaseTable(DeclarativeBase):
    pass


class State(BaseTable):
    """Represent the state of a node in relation to a task."""

    __tablename__ = "state"

    task: Mapped[str] = mapped_column(primary_key=True)
    node: Mapped[str] = mapped_column(primary_key=True)
    hash_: Mapped[str]


def create_database(url: str) -> None:
    """Create the database."""
    engine = create_engine(url)
    BaseTable.metadata.create_all(bind=engine)
    DatabaseSession.configure(bind=engine)


def _create_or_update_state(first_key: str, second_key: str, hash_: str) -> None:
    """Create or update a state."""
    with DatabaseSession() as session:
        state_in_db = session.get(State, (first_key, second_key))
        if not state_in_db:
            session.add(State(task=first_key, node=second_key, hash_=hash_))
        else:
            state_in_db.hash_ = hash_
        session.commit()


def update_states_in_database(session: Session, task_signature: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(session.dag, task_signature):
        node = session.dag.nodes[name].get("task") or session.dag.nodes[name]["node"]
        hash_ = node.state()
        _create_or_update_state(task_signature, node.signature, hash_)


def has_node_changed(task: PTask, node: PTask | PNode, state: str | None) -> bool:
    """Indicate whether a single dependency or product has changed."""
    # If node does not exist, we receive None.
    if state is None:
        return True

    with DatabaseSession() as session:
        db_state = session.get(State, (task.signature, node.signature))

    # If the node is not in the database.
    if db_state is None:
        return True

    return state != db_state.hash_
