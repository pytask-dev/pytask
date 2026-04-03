# lock

Inspect and update recorded task state in the lockfile.

## Usage

```bash
pytask lock SUBCOMMAND [OPTIONS] [PATHS]
```

Subcommands:

- `accept`: Accept the current state for selected tasks.
- `reset`: Remove recorded state for selected tasks.
- `clean`: Remove stale lockfile entries which no longer correspond to collected tasks.

If no selectors are provided for `accept` or `reset`, the command applies to all
collected tasks in the provided paths.

## Examples

```bash
# Preview which selected tasks would be accepted.
pytask lock accept -k train --dry-run

# Accept the current state for all collected tasks in the current directory.
pytask lock accept --yes

# Also include descendants of the selected tasks.
pytask lock accept -k train --with-descendants

# Restrict the staleness decision to task and dependency changes.
pytask lock accept -k train --run-on task_change,dependency_change

# Reset recorded state for selected tasks.
pytask lock reset -k train --yes

# Remove stale entries from the lockfile.
pytask lock clean --yes
```

## Subcommands

### accept

Accept the current state for selected tasks without executing them.

```bash
pytask lock accept [OPTIONS] [PATHS]
```

Options:

--8<-- "docs/source/_static/md/commands/lock-accept-options.md"

### reset

Remove recorded state for selected tasks.

```bash
pytask lock reset [OPTIONS] [PATHS]
```

Options:

--8<-- "docs/source/_static/md/commands/lock-reset-options.md"

### clean

Remove stale lockfile entries.

```bash
pytask lock clean [OPTIONS] [PATHS]
```

Options:

--8<-- "docs/source/_static/md/commands/lock-clean-options.md"

## Interaction Modes

- Default: Run interactively, show the planned changes, and step through them one by one
    with an interactive selector for each task or lockfile entry.
- `--dry-run`: Show the planned changes without writing them.
- `--yes`: Apply the planned changes without prompting.

The options `--dry-run` and `--yes` are mutually exclusive.

## Related

- [Reconciling Lockfile State](../how_to_guides/reconciling_lockfile_state.md)
- [Selecting tasks](../tutorials/selecting_tasks.md)
- [Making Tasks Persist](../tutorials/making_tasks_persist.md)
- [Lockfile](../reference_guides/lockfile.md)
