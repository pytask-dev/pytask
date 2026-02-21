# Plan: Lockfile Review Follow-ups

## Goals
- Align implementation with intended backend behavior (DB read-only when no lockfile; lockfile-only afterwards).
- Fix correctness and compatibility risks in the lockfile implementation.
- Close documentation and test gaps.

## Findings to Address
1. **DB writes continue after lockfile exists**
   - `update_states()` always calls `_db_update_states(...)` even when `pytask.lock` is present.
   - **Action:** Guard `_db_update_states` so DB writes stop once the lockfile exists.
2. **PythonNode ID collisions**
   - `node_info.path` segments are joined with `"-"`; this can collide for certain tuples.
   - **Action:** Encode `node_info.path` losslessly (e.g., JSON/msgspec with a stable prefix or length-prefix segments).
3. **Decode error handling**
   - Initial decode can raise `msgspec.DecodeError` without a clean `LockfileError`.
   - **Action:** Wrap the first decode in the same error handling as the typed decode.
4. **Docs mismatch**
   - Docs say DB is only consulted when no lockfile exists, but DB is still created/updated.
   - **Action:** Update docs to match behavior after gating; clarify skip behavior and lockfile updates.
5. **Tests missing**
   - No test that lockfile-only skipping works when DB changes.
   - No test for DB no-write after lockfile exists.
   - No portability tests for ID generation (relative paths, `..`, `UPath`).
   - No test for malformed lockfile error behavior.

## Tasks
1. **Backend gating**
   - Implement guard in `update_states()` so `_db_update_states` is skipped once a lockfile exists.
   - Optionally skip DB creation when `pytask.lock` already exists (confirm desired behavior first).
2. **ID encoding**
   - Update `build_portable_node_id()` to encode `node_info.path` without collisions.
   - Add unit tests covering ambiguous tuples that would collide under `"-"` join.
3. **Error handling**
   - Wrap first decode in `read_lockfile()` with `msgspec.DecodeError` handling.
4. **Docs**
   - Align lockfile + configuration docs with actual behavior after gating.
5. **Tests**
   - Add regression tests for lockfile-only skip behavior, DB no-write after lockfile, portability IDs, and malformed lockfile formats.
