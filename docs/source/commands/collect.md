# collect

Collect tasks and report information about them.

## Usage

```bash
pytask collect [OPTIONS] [PATHS]
```

## Examples

```bash
# Show collected tasks.
pytask collect

# Also show dependencies and products.
pytask collect --nodes

# Select collected tasks by marker expression.
pytask collect -m "not slow"
```

## Arguments

--8<-- "docs/source/_static/md/commands/collect-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/collect-options.md"

## Related

- [Collecting tasks](../tutorials/collecting_tasks.md)
- [Selecting tasks](../tutorials/selecting_tasks.md)
