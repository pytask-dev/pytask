# Portability

This guide explains what you need to do to move a pytask project between machines and
why the lockfile is central to that process.

```{seealso}
The lockfile format and behavior are documented in the
[reference guide](../reference_guides/lockfile.md).
```

## How to port a project

Use this checklist when you move a project to another machine or environment.

1. **Update state once on the source machine.**

   Run a normal build so `pytask.lock` is up to date:

   ```console
   $ pytask build
   ```

   If you already have a recent lockfile and up-to-date outputs, you can skip this step.

1. **Ship the right files.**

   Commit `pytask.lock` to your repository and move it with the project. In practice,
   you should move:

   - the project files tracked in version control (source, configuration, data inputs
     and `pytask.lock`)
   - the build artifacts you want to reuse (often in `bld/` if you follow the tutorial
     layout)
   - the `.pytask` folder in case you are using the data catalog and it manages some of
     the files

1. **Files outside the project**

   If you have files outside the project root (the folder with the `pyproject.toml`
   file), you need to make sure that the same relative layout exists on the target
   machine.

1. **Run pytask on the target machine.**

   When states match, tasks are skipped. When they differ, tasks run and the lockfile is
   updated.

## What makes a project portable

There are two things that must stay stable across machines:

First, task and node IDs must be stable. An ID is the unique identifier that ties a task
or node to an entry in `pytask.lock`. pytask builds these IDs from project-relative
paths anchored at the project root, so most users do not need to do anything. If you
implement custom nodes, make sure their IDs remain project-relative and stable across
machines.

Second, state values must be portable. The lockfile stores opaque state strings from
`PNode.state()` and `PTask.state()`, and pytask uses them to decide whether a task is up
to date. Content hashes are portable; timestamps or absolute paths are not. This mostly
matters when you define custom nodes or custom hash functions.

## Tips for stable state values

- Prefer file content hashes over timestamps for custom nodes.
- For `PythonNode` values that are not natively stable, provide a custom hash function.
- Avoid machine-specific paths or timestamps in custom `state()` implementations.

```{seealso}
For custom nodes, see [Writing custom nodes](writing_custom_nodes.md).
For hashing guidance, see
[Hashing inputs of tasks](hashing_inputs_of_tasks.md).
```

## Cleaning up the lockfile

`pytask.lock` is updated incrementally. Entries are only replaced when the corresponding
tasks run. If tasks are removed or renamed, their old entries remain as stale data and
are ignored.

To clean up stale entries without deleting the file, run:

```console
$ pytask build --clean-lockfile
```

This rewrites the lockfile after a successful build with only the currently collected
tasks and their current state values.
