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
    uv run --group typing --group test --isolated ty check

# Run linting
lint:
    uvx prek run -a

# Run all checks (format, lint, typing, test)
check: lint typing test

# Build documentation
docs:
    uv run --group plugin-list python scripts/update_plugin_list.py
    uv run --group docs zensical build

# Serve documentation with auto-reload
docs-serve:
    uv run --group plugin-list python scripts/update_plugin_list.py
    uv run --group docs zensical serve -a 127.0.0.1:8000

# Run tests with lowest dependency resolution (like CI)
test-lowest:
    uv run --python 3.10 --group test --resolution lowest-direct pytest --nbmake

# Run tests with highest dependency resolution (like CI)
test-highest:
    uv run --python 3.14 --group test --resolution highest pytest --nbmake -n auto
