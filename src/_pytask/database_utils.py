"""This module contains utilities for the database."""
from __future__ import annotations

import hashlib

from _pytask.dag_utils import node_and_neighbors
from _pytask.nodes import Task
from _pytask.session import Session
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import declarative_base


__all__ = ["create_database", "update_states_in_database", "DatabaseSession"]


DatabaseSession = sessionmaker()


Base = declarative_base()


class State(Base):
    """Represent the state of a node in relation to a task."""

    __tablename__ = "state"

    task = Column(String, primary_key=True)
    node = Column(String, primary_key=True)
    modification_time = Column(String)
    file_hash = Column(String)


def create_database(url: str) -> None:
    """Create the database."""
    try:
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)
        DatabaseSession.configure(bind=engine)
    except Exception:
        raise


def _create_or_update_state(
    first_key: str, second_key: str, modification_time: str, file_hash: str
) -> None:
    """Create or update a state."""
    with DatabaseSession() as session:
        state_in_db = session.get(State, (first_key, second_key))

        if not state_in_db:
            session.add(
                State(
                    task=first_key,
                    node=second_key,
                    modification_time=modification_time,
                    file_hash=file_hash,
                )
            )
        else:
            state_in_db.modification_time = modification_time
            state_in_db.file_hash = file_hash

        session.commit()


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
