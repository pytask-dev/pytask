# Move a Project to Another Machine

This guide teaches you how to move a pytask project to another machine or environment
and reuse existing outputs where possible.

## Update the lockfile on the source machine

Run a normal build with [`pytask build`](../reference_guides/commands.md#pytask-build)
before moving the project with its `pytask.lock` and files and outputs are up-to-date:

```console
$ pytask build
```

## Move the project files and reusable outputs

If you have not done it yet, commit `pytask.lock` to your repository and move it with
the project. In practice, move:

- the project files tracked in version control, including source files, configuration,
    data inputs, and `pytask.lock`
- the build artifacts you want to reuse, often in `bld/` if you follow the tutorial
    layout
- the `.pytask` folder if you use the data catalog and it manages some of your files

## Keep external files in the same relative layout

If tasks use files outside the project root, keep the same relative layout on the target
machine. The project root is the folder with the `pyproject.toml` file.

For example, if a task reads `../shared/input.csv` from the source machine, the moved
project also needs a readable `../shared/input.csv` next to the project root on the
target machine.

## Run pytask on the target machine

After you moved the project to the target machine, run pytask to build the project:

```console
$ pytask build
```

Assuming that the project was fully built before the move, pytask will not rebuild the
project and skip all tasks.

## Clean stale lockfile entries

If you removed, renamed, or moved tasks before transferring the project, clean up stale
lockfile entries on the source machine before you move the project:

```console
$ pytask build --clean-lockfile
```

This rewrites the lockfile after a successful build with only the currently collected
tasks and their current state values.

## If your project uses custom nodes

Make sure custom node IDs and state values stay stable across machines:

- Use project-relative IDs instead of absolute paths.
- Prefer file content hashes over timestamps.
- Avoid machine-specific paths or timestamps in custom
    [`state()`](../reference_guides/api/nodes_and_tasks.md#pytask.PNode.state)
    implementations.
- Provide a custom hash function for
    [`PythonNode`](../reference_guides/api/nodes_and_tasks.md#pytask.PythonNode) values
    that are not natively stable.

Most projects that only use built-in nodes do not need extra work here.

!!! seealso

    The lockfile format and behavior are documented in the
    [reference guide](../reference_guides/lockfile.md). For custom nodes, see
    [Writing custom nodes](writing_custom_nodes.md). For hashing guidance, see
    [Hashing inputs of tasks](hashing_inputs_of_tasks.md).
