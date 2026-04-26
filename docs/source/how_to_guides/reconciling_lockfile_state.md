# Reconciling Lockfile State

Use [`pytask lock`](../reference_guides/commands.md#pytask-lock) when the current files
in the project are already correct and only the recorded state in `pytask.lock` needs to
catch up.

This is an advanced workflow. Most of the time,
[`pytask build`](../reference_guides/commands.md#pytask-build) is the right command.
Reach for `pytask lock` when you want to change the lockfile without executing tasks.

!!! warning

    `pytask lock` is a sharp tool. It updates recorded state without proving that the files
    were produced by the current task definitions.

## When is this useful?

Typical situations are:

- You reformatted or reorganized a task file and do not want to rerun an expensive task.
- You renamed or moved a task and want to accept the current outputs for the new task.
- You produced outputs manually or elsewhere and now want to register them in the
    lockfile.
- You deleted or renamed tasks and want to remove their stale lockfile entries.

## Preview changes first

By default, `pytask lock` runs interactively. It shows the planned changes and then asks
for confirmation one by one. Only entries which would actually change appear in the
prompt sequence.

To preview changes without writing them, use `--dry-run`:

--8<-- "docs/source/_static/md/lock-accept-dry-run.md"

To apply all planned changes without prompting, use `--yes`:

```console
$ pytask lock accept -k train --yes
```

## Accept the current state

Use [`pytask lock accept`](../reference_guides/commands.md#pytask-lock-accept) when the
current dependencies, products, and task definition are already correct and should
become the new recorded state.

--8<-- "docs/source/_static/md/lock-accept-interactive.md"

If no selectors are provided, `pytask lock accept` applies to all collected tasks in the
provided paths.

If selectors are provided with `-k` or `-m`, `accept` automatically includes the
ancestors of the selected tasks. This is useful when you target a downstream task and
want the accepted state to stay consistent with its upstream dependencies.

```console
$ pytask lock accept -k evaluate
```

In this example, `pytask` accepts `evaluate` and its ancestors. It does not
automatically include descendants. If you want to accept a wider part of the DAG, widen
the task selection yourself.

```console
$ pytask lock accept -k "train or evaluate"
```

If a selected task is missing a required dependency or product, the command fails
instead of accepting incomplete state.

## Reset recorded state

Use [`pytask lock reset`](../reference_guides/commands.md#pytask-lock-reset) to remove
recorded state for selected tasks.

```console
$ pytask lock reset -k train
```

Unlike `accept`, `reset` works on the exact selected tasks. It does not automatically
include ancestors.

On the next build, `pytask` determines again whether these tasks require execution. This
is useful when state was accepted too broadly or when you want a specific task to be
reconsidered from scratch.

## Remove stale lockfile entries

Use [`pytask lock clean`](../reference_guides/commands.md#pytask-lock-clean) to remove
entries from the lockfile which no longer correspond to collected tasks in the current
project.

--8<-- "docs/source/_static/md/lock-clean.md"

This is useful after deleting, renaming, or moving tasks when old entries should no
longer remain in the lockfile.

## Example workflow

One common workflow looks like this:

1. Run a normal build once.
1. Change a task file in a way that should not force a rerun.
1. Accept the current state.
1. Verify that a later build skips the task.
1. Reset the task if you want `pytask` to reconsider it again.

```console
$ pytask build
$ pytask lock accept -k train --yes
$ pytask build
$ pytask lock reset -k train --yes
$ pytask build
```

After `accept`, the next build skips unchanged tasks according to the updated lockfile.
After `reset`, the selected tasks are reconsidered on the next build.

## Be explicit about scope

Start with narrow task selections, preview changes with `--dry-run`, and widen the
selection only when needed.

This is especially important for `accept`: it is often better to accept a small part of
the DAG first and then inspect the result than to update the whole project at once.

## Related

- [`pytask lock`](../reference_guides/commands.md#pytask-lock)
- [`pytask build`](../reference_guides/commands.md#pytask-build)
- [Portability](portability.md)
- [The lockfile](../reference_guides/lockfile.md)
