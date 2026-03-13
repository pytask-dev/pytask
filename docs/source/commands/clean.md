# clean

Clean provided paths by removing files unknown to pytask.

## Usage

```bash
pytask clean [OPTIONS] [PATHS]
```

## Examples

```bash
# Dry-run cleanup.
pytask clean

# Remove unknown files immediately.
pytask clean --mode force

# Exclude a path pattern.
pytask clean --exclude obsolete_folder
```

## Arguments

--8<-- "docs/source/_static/md/commands/clean-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/clean-options.md"

## Related

- [Cleaning projects](../tutorials/cleaning_projects.md)
- [Configuration](../reference_guides/configuration.md)
