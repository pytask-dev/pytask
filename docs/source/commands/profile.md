# profile

Show information about resource consumption.

## Usage

```bash
pytask profile [OPTIONS] [PATHS]
```

## Examples

```bash
# Show profiling information from previous successful runs.
pytask profile

# Export profiling information as JSON.
pytask profile --export json

# Export profiling information as CSV.
pytask profile --export csv
```

## Arguments

--8<-- "docs/source/_static/md/commands/profile-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/profile-options.md"

## Related

- [Profiling tasks](../tutorials/profiling_tasks.md)
