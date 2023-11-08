"""Contains utilities for the database."""
from __future__ import annotations

from typing import TYPE_CHECKING

from _pytask.dag_utils import node_and_neighbors
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from _pytask.session import Session


__all__ = [
    "BaseTable",
    "DatabaseSession",
    "create_database",
    "update_states_in_database",
]


DatabaseSession = sessionmaker()


BaseTable = declarative_base()


class State(BaseTable):  # type: ignore[valid-type, misc]
    """Represent the state of a node in relation to a task."""

    __tablename__ = "state"

    task = Column(String, primary_key=True)
    node = Column(String, primary_key=True)
    hash_ = Column(String)


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
            state_in_db.hash_ = hash_  # type: ignore[assignment]
        session.commit()


def update_states_in_database(session: Session, task_signature: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(session.dag, task_signature):
        node = session.dag.nodes[name].get("task") or session.dag.nodes[name]["node"]
        hash_ = node.state()
        _create_or_update_state(task_signature, node.signature, hash_)
