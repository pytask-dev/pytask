# AGENTS

Guidance for coding agents working in this repository.

## Tooling

- Use `uv` for Python environments, dependencies, and running commands.
- Use `just` as the primary task runner.
- Use `rg` for fast code search.
- `ast-grep` and `fastmod` are available for structural refactors.
- `pixi` is available when needed.

## Setup

- Install dependencies:
  - `just install`
  - or `uv sync --all-groups`

## Validation Commands

- Lint:
  - `just lint`
- Type checking:
  - `just typing`
- Tests:
  - `just test`
- Full verification:
  - `just check`

For targeted tests, prefer:

- `uv run --group test pytest tests/path/to/test_file.py -k "pattern"`
