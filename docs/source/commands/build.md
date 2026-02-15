# build

Collect tasks, execute them, and report the results.

## Usage

```bash
pytask build [OPTIONS] [PATHS]
```

`pytask` without a subcommand runs `build` by default.

## Examples

```bash
# Run the project in the current directory.
pytask build

# Select tasks by expression.
pytask build -k random_data

# Show what would run without executing tasks.
pytask build --dry-run
```

## Arguments

--8<-- "docs/source/_static/md/commands/build-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/build-options.md"

## Related

- [Invoking pytask](../tutorials/invoking_pytask.md)
- [Selecting tasks](../tutorials/selecting_tasks.md)
- [Debugging](../tutorials/debugging.md)
- [Configuration](../reference_guides/configuration.md)
