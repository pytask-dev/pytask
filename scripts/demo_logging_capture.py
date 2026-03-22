"""Run a small demo project for log capture and export.

Usage
-----
uv run python scripts/demo_logging_capture.py

The script creates a temporary demo project, runs a few `pytask` commands against it,
prints their output, and leaves the files on disk for inspection.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    demo_root = Path(tempfile.mkdtemp(prefix="pytask-logging-demo-"))
    _write_line(f"Demo project: {demo_root}")
    _write_line()

    _write_demo_project(demo_root)

    _run_demo_case(
        repo_root=repo_root,
        title="Show only captured logs for the failing task",
        args=[
            str(demo_root),
            "--log-level=INFO",
            "--log-date-format=%H:%M:%S",
            "--log-format=%(asctime)s %(levelname)-8s %(name)s:%(message)s",
            "--show-capture=log",
        ],
    )

    _run_demo_case(
        repo_root=repo_root,
        title="Show logs, stdout, and stderr, and export logs to a file",
        args=[
            str(demo_root),
            "--force",
            "--log-level=INFO",
            "--log-date-format=%H:%M:%S",
            "--show-capture=all",
            "--log-file=build.log",
            "--log-format=%(asctime)s %(levelname)-8s %(name)s:%(message)s",
        ],
    )

    log_file = demo_root.joinpath("build.log")
    if log_file.exists():
        _write_line("=" * 80)
        _write_line(f"Exported log file: {log_file}")
        _write_line("=" * 80)
        _write(log_file.read_text())
        _write_line()

    _write_line("=" * 80)
    _write_line("You can rerun the demo project manually with commands like:")
    _write_line(f"  cd {repo_root}")
    _write_line(
        "  uv run python -m pytask "
        f"{demo_root} --log-level=INFO --show-capture=all --log-file=build.log"
    )
    _write_line("=" * 80)


def _write_demo_project(demo_root: Path) -> None:
    source = """
    from __future__ import annotations

    import logging
    import sys
    from pathlib import Path

    logger = logging.getLogger("demo")


    def task_prepare_report(produces=Path("report.txt")):
        logger.info("preparing report.txt")
        produces.write_text("report created\\n")


    def task_publish_report(
        depends_on=Path("report.txt"), produces=Path("published.txt")
    ):
        logger.warning("publishing report is about to fail")
        print("stdout from task_publish_report")
        sys.stderr.write("stderr from task_publish_report\\n")
        raise RuntimeError("simulated publish failure")
    """
    demo_root.joinpath("task_logging_demo.py").write_text(textwrap.dedent(source))


def _run_demo_case(*, repo_root: Path, title: str, args: list[str]) -> None:
    command = [sys.executable, "-m", "pytask", *args]
    rendered_command = " ".join(command)

    _write_line("=" * 80)
    _write_line(title)
    _write_line(rendered_command)
    _write_line("=" * 80)

    result = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
    )

    if result.stdout:
        _write(result.stdout)
        if not result.stdout.endswith("\n"):
            _write_line()
    if result.stderr:
        _write_line("-" * 80)
        _write_line("stderr")
        _write_line("-" * 80)
        _write(result.stderr)
        if not result.stderr.endswith("\n"):
            _write_line()

    _write_line("-" * 80)
    _write_line(f"exit code: {result.returncode}")
    _write_line()


def _write(text: str) -> None:
    sys.stdout.write(text)


def _write_line(text: str = "") -> None:
    sys.stdout.write(f"{text}\n")


if __name__ == "__main__":
    main()
