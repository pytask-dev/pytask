# Reconciling lockfile state

The [`lock`](../commands/lock.md) command is useful when the current project state
should be reconciled with the lockfile without running tasks.

This is an advanced workflow. Most of the time, [`pytask build`](../commands/build.md)
is the right command. Reach for `pytask lock` when the current files are already correct
and only the recorded state needs to catch up.

## When is this useful?

Typical situations are:

- You renamed or moved a task and want to accept the current outputs for the new task.
- You reformatted a task file and do not want to rerun an expensive task.
- You produced outputs manually or elsewhere and now want to register them in the
    lockfile.
- You want to remove old lockfile entries after deleting or renaming tasks.

## Preview changes first

By default, `pytask lock` runs interactively. It shows the planned changes and then
steps through them one by one.

To preview changes without writing them, use `--dry-run`.

--8<-- "docs/source/_static/md/lock-accept-dry-run.md"

To apply changes without prompting, use `--yes`.

```bash
pytask lock accept -k train --yes
```

## Accept the current state for selected tasks

Use `pytask lock accept` when the current dependencies and products are already correct
and should become the new recorded state.

--8<-- "docs/source/_static/md/lock-accept-interactive.md"

If no selectors are provided, `pytask lock accept` applies to all collected tasks in the
provided paths.

By default, the command applies only to the selected tasks. It does not automatically
include ancestors or descendants.

If you want to accept a wider part of the DAG, widen the task selection yourself.

```bash
pytask lock accept -k "train or evaluate"
```

You can also expand the selection structurally.

```bash
pytask lock accept -k train --with-descendants
```

```bash
pytask lock accept -k evaluate --with-ancestors
```

If a selected task is missing a required dependency or product, the command fails for
that task.

## Control which changes matter

`pytask lock accept` can use `--run-on` to decide which kinds of changes are considered
when determining whether a task would normally require execution.

Supported values are:

- `task_change`
- `dependency_change`
- `product_change`

For example, if only changes to the task definition and dependencies should matter for
the current command, you can write:

```bash
pytask lock accept -k train --run-on task_change,dependency_change
```

This is useful when you want to treat one kind of change as relevant for the current
operation while ignoring another one.

## Reset recorded state for selected tasks

Use `pytask lock reset` when recorded state for selected tasks should be removed.

```bash
pytask lock reset -k train
```

On the next build, pytask will determine again whether these tasks require execution.

This is useful when state was accepted too broadly or when you want selected tasks to be
reconsidered from scratch.

## Remove stale lockfile entries

Use `pytask lock clean` to remove entries from the lockfile which no longer correspond
to collected tasks in the current project.

```bash
pytask lock clean
```

--8<-- "docs/source/_static/md/lock-clean.md"

This is useful after deleting, renaming, or moving tasks when old entries should no
longer remain in the lockfile.

## Be explicit about scope

`pytask lock` is a sharp tool. It changes recorded state without executing tasks.

Use narrow task selections first, preview changes with `--dry-run`, and widen the
selection only when needed.

## Related

- [`pytask lock`](../commands/lock.md)
- [Making Tasks Persist](../tutorials/making_tasks_persist.md)
- [Task Execution Model](../explanations/execution_policies.md)
- [Lockfile](../reference_guides/lockfile.md)
