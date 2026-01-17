"""State handling for lockfile and database backends."""

from __future__ import annotations

from typing import TYPE_CHECKING

from _pytask.database_utils import get_node_change_info as _db_get_node_change_info
from _pytask.database_utils import has_node_changed as _db_has_node_changed
from _pytask.database_utils import update_states_in_database as _db_update_states
from _pytask.lockfile import LockfileState
from _pytask.lockfile import build_portable_node_id
from _pytask.lockfile import build_portable_task_id
from _pytask.node_protocols import PTask

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode
    from _pytask.session import Session


def _get_lockfile_state(session: Session) -> LockfileState | None:
    return session.config.get("lockfile_state")


def has_node_changed(
    session: Session, task: PTask, node: PTask | PNode, state: str | None
) -> bool:
    lockfile_state = _get_lockfile_state(session)
    if lockfile_state and lockfile_state.use_lockfile_for_skip:
        if state is None:
            return True
        task_id = build_portable_task_id(task, lockfile_state.root)
        if node is task or (
            hasattr(node, "signature") and node.signature == task.signature
        ):
            entry = lockfile_state.get_task_entry(task_id)
            if entry is None:
                return True
            return state != entry.state
        node_id = (
            build_portable_task_id(node, lockfile_state.root)
            if isinstance(node, PTask)
            else build_portable_node_id(node, lockfile_state.root)
        )
        stored_state = lockfile_state.get_node_state(task_id, node_id)
        if stored_state is None:
            return True
        return state != stored_state
    return _db_has_node_changed(task=task, node=node, state=state)


def get_node_change_info(
    session: Session, task: PTask, node: PTask | PNode, state: str | None
) -> tuple[bool, str, dict[str, str]]:
    lockfile_state = _get_lockfile_state(session)
    if not (lockfile_state and lockfile_state.use_lockfile_for_skip):
        return _db_get_node_change_info(task=task, node=node, state=state)

    details: dict[str, str] = {}
    if state is None:
        return True, "missing", details

    task_id = build_portable_task_id(task, lockfile_state.root)
    is_task = node is task or (
        hasattr(node, "signature") and node.signature == task.signature
    )
    if is_task:
        entry = lockfile_state.get_task_entry(task_id)
        if entry is None:
            return True, "not_in_db", details
        stored_state = entry.state
    else:
        node_id = (
            build_portable_task_id(node, lockfile_state.root)
            if isinstance(node, PTask)
            else build_portable_node_id(node, lockfile_state.root)
        )
        stored_state = lockfile_state.get_node_state(task_id, node_id)
        if stored_state is None:
            return True, "not_in_db", details

    if state != stored_state:
        details["old_hash"] = stored_state
        details["new_hash"] = state
        return True, "changed", details
    return False, "unchanged", details


def update_states(session: Session, task: PTask) -> None:
    if session.dag is None:
        return
    lockfile_state = _get_lockfile_state(session)
    if lockfile_state is not None:
        lockfile_state.update_task(session, task)
        return
    _db_update_states(session, task.signature)
