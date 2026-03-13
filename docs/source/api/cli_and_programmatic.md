# CLI Imports

This page documents the public CLI-related imports from `pytask`.

For command usage and options, see the [CLI reference](../commands/index.md).

## Command Line Entry Point

::: pytask.cli
    options:
      show_root_heading: true
      show_signature: true

## CLI Types

::: pytask.ColoredCommand
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"
::: pytask.ColoredGroup
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"
::: pytask.EnumChoice
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"
