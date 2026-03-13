# markers

Show all registered markers.

## Usage

```bash
pytask markers [OPTIONS] [PATHS]
```

## Examples

```bash
# List all registered markers.
pytask markers

# Load custom marker definitions from a hooks module.
pytask markers --hook-module hooks.py
```

## Arguments

--8<-- "docs/source/_static/md/commands/markers-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/markers-options.md"

## Related

- [Markers](../tutorials/markers.md)
- [Extending pytask](../how_to_guides/extending_pytask.md)
