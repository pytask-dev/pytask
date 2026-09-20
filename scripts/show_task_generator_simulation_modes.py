# ruff: noqa: T201
"""Show how task generators behave in dry-run and explain modes.

Run this script from the repository root with

    uv run python scripts/show_task_generator_simulation_modes.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

TASK_MODULE = """
from pathlib import Path

from pytask import task


@task(is_generator=True)
def task_generator():
    counter = Path(__file__).with_name("generator-runs.txt")
    previous_runs = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(previous_runs + 1))

    @task
    def task_generated(
        produces=Path(__file__).with_name("generated-task-ran.txt"),
    ):
        produces.write_text("ran")
"""


def run_case(root: Path, mode: str) -> None:
    """Run one mode in an isolated directory and print the observable behavior."""
    case_dir = root / mode
    case_dir.mkdir()
    case_dir.joinpath("task_module.py").write_text(
        textwrap.dedent(TASK_MODULE), encoding="utf-8"
    )

    command = [sys.executable, "-m", "pytask", f"--{mode}", str(case_dir)]
    environment = {**os.environ, "NO_COLOR": "1", "PYTHONUTF8": "1"}
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )

    counter = case_dir / "generator-runs.txt"
    generated_product = case_dir / "generated-task-ran.txt"

    print(f"\n{mode.upper()}")
    print(f"command: {' '.join(command)}")
    print(completed.stdout.strip())
    if completed.stderr:
        print("stderr:")
        print(completed.stderr.strip())
    print(f"process exit code: {completed.returncode}")
    print(f"generator body runs: {counter.read_text(encoding='utf-8')}")
    print(f"generated task ran: {generated_product.exists()}")


def main() -> None:
    """Run both simulation modes without sharing build artifacts."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="pytask-generator-modes-") as directory:
        root = Path(directory)
        run_case(root, "dry-run")
        run_case(root, "explain")


if __name__ == "__main__":
    main()
