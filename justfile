# Install all dependencies
install:
    uv sync --all-groups

# Run tests
test *FLAGS:
    uv run --group test pytest {{FLAGS}}

# Run tests with coverage
test-cov *FLAGS:
    uv run --group test pytest --nbmake --cov=src --cov=tests --cov-report=xml -n auto {{FLAGS}}

# Run type checking
typing:
    uv run --group typing --group test ty check src/ tests/

# Run linting
lint:
    uvx prek run -a

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
    uv run --python 3.10 --group test --resolution lowest-direct pytest --nbmake

# Run tests with highest dependency resolution (like CI)
test-highest:
    uv run --python 3.14 --group test --resolution highest pytest --nbmake -n auto
