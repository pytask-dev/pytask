# Portability

This guide explains how to keep pytask state portable across machines.

## Two Portability Concerns

1. **Portable IDs**

   - The lockfile stores task and node IDs.
   - IDs must be project‑relative and stable across machines.
   - pytask builds these IDs from the project root; no action required for most users.

1. **Portable State Values**

   - `state` is opaque and comes from `PNode.state()` / `PTask.state()`.
   - Content hashes are portable; timestamps or absolute paths are not.
   - Custom nodes should avoid machine‑specific paths in `state()`.

## Tips

- Commit `pytask.lock` to your repository. If you ship the repository together with the
  build artifacts (for example, a zipped project folder including `pytask.lock` and the
  produced files), you can move it to another machine and runs will skip recomputation.
- Prefer file content hashes over timestamps for custom nodes.
- For `PythonNode` values that are not natively stable, provide a custom hash function.
- If inputs live outside the project root, IDs will include `..` segments to remain
  relative; this is expected.

## Cleaning Up the Lockfile

`pytask.lock` is updated incrementally. Entries are only replaced when the corresponding
tasks run. If tasks are removed or renamed, their old entries remain as stale data and
are ignored.

To clean up stale entries without deleting the file, run:

```
pytask build --clean-lockfile
```

This rewrites the lockfile after a successful build with only the currently collected
tasks and their current state values.

## Legacy SQLite

SQLite is the old state format. It is used only when no lockfile exists, and the
lockfile is written during that run. Subsequent runs rely on the lockfile and do not
update database state.
