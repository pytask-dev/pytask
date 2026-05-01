# Update the Lockfile to Match Project State

Use [`pytask lock`](../reference_guides/commands.md#pytask-lock) when the current files
and outputs in the project are already correct, but the recorded state in `pytask.lock`
needs to catch up. This can happen after refactoring task files, moving or renaming
tasks, producing outputs outside of pytask, or deleting tasks.

## Accept current files and outputs

Use [`pytask lock accept`](../reference_guides/commands.md#pytask-lock-accept) when the
current dependencies, products, and task definition are already correct and should
become the new recorded state.

Preview the changes without writing them with `--dry-run`:

--8<-- "docs/source/_static/md/lock-accept-dry-run.md"

Then accept the planned changes interactively:

--8<-- "docs/source/_static/md/lock-accept-interactive.md"

Add `--yes` to apply all planned changes without prompting:

```console
$ pytask lock accept -k train --yes
```

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

Run a build afterwards to check that unchanged tasks are skipped according to the
updated lockfile.

```console
$ pytask build
```

## Reset state for selected tasks

Use [`pytask lock reset`](../reference_guides/commands.md#pytask-lock-reset) to remove
recorded state for selected tasks when state was accepted too broadly or when specific
tasks should be reconsidered from scratch.

```console
$ pytask lock reset -k train
```

Unlike `accept`, `reset` with a selector works on the exact selected tasks. It does not
automatically include ancestors.

Preview the reset with `--dry-run` if you want to check the affected tasks first:

```console
$ pytask lock reset -k train --dry-run
```

Add `--yes` to remove all planned entries without prompting:

```console
$ pytask lock reset -k train --yes
```

If no selectors are provided, `pytask lock reset` removes the recorded state for all
collected tasks in the provided paths.

Run a build afterwards so `pytask` determines again whether the selected tasks require
execution.

```console
$ pytask build
```

## Remove stale entries for deleted or moved tasks

Use [`pytask lock clean`](../reference_guides/commands.md#pytask-lock-clean) to remove
entries from the lockfile which no longer correspond to collected tasks in the current
project. This is useful after deleting, renaming, or moving tasks when old entries
should no longer remain in the lockfile.

Preview stale entries without writing them with `--dry-run`:

```console
$ pytask lock clean --dry-run
```

Then remove stale entries interactively:

--8<-- "docs/source/_static/md/lock-clean.md"

Add `--yes` to remove all stale entries without prompting:

```console
$ pytask lock clean --yes
```

`clean` only removes entries for tasks which are no longer collected. It does not accept
or update the current state of collected tasks.

## Related

- [`pytask lock`](../reference_guides/commands.md#pytask-lock)
- [`pytask build`](../reference_guides/commands.md#pytask-build)
- [Portability](portability.md)
- [The lockfile](../reference_guides/lockfile.md)
