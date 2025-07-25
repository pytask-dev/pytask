# Default recipe to display available commands
default:
    @just --list

# Install all dependencies
install:
    uv sync --all-groups

# Run tests
test:
    uv run --group test pytest

# Run tests with coverage
test-cov:
    uv run --group test pytest --nbmake --cov=src --cov=tests --cov-report=xml -n auto

# Run tests with notebook validation
test-nb:
    uv run --group test pytest --nbmake -n auto

# Run type checking
typing:
    uv run --group typing mypy check

# Run type checking on notebooks
typing-nb:
    uv run --group typing nbqa mypy --ignore-missing-imports .

# Run linting
lint:
    uvx --with pre-commit-uv pre-commit run -a

# Run all checks (format, lint, typing, test)
check: lint typing test

# Build documentation
docs:
    uv run --group docs sphinx-build docs/source docs/build

# Serve documentation with auto-reload
docs-serve:
    uv run --group docs sphinx-autobuild docs/source docs/build

# Run tests with lowest dependency resolution (like CI)
test-lowest:
    uv run --group test --resolution lowest-direct pytest --nbmake -n auto

# Run tests with highest dependency resolution (like CI)
test-highest:
    uv run --group test --resolution highest pytest --nbmake -n auto
