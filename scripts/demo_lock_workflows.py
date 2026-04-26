"""Demonstrate end-to-end lock workflows with small temporary projects.

Run with

    uv run python scripts/demo_lock_workflows.py

or select one scenario with

    uv run python scripts/demo_lock_workflows.py --scenario golden-path

Use ``--keep`` to keep the temporary project directories for inspection.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

import click


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    callback_name: str


SCENARIOS = (
    Scenario(
        name="golden-path",
        description=(
            "Build a task, modify it, accept the change, verify that build skips it, "
            "reset it, and verify that build executes it again."
        ),
        callback_name="scenario_golden_path",
    ),
    Scenario(
        name="accept-ancestors",
        description=(
            "Target a downstream task, accept it, and show that ancestors are accepted "
            "implicitly while descendants are not."
        ),
        callback_name="scenario_accept_ancestors",
    ),
    Scenario(
        name="clean-subtractive",
        description=(
            "Remove a stale task, add a new one, run lock clean, and show that clean "
            "removes stale entries without accepting new tasks."
        ),
        callback_name="scenario_clean_subtractive",
    ),
)


def _write(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip())


def _run(project: Path, *args: str) -> None:
    cmd = [sys.executable, "-m", "pytask", *args, project.as_posix()]
    click.echo()
    click.echo(f"$ {' '.join(cmd)}")
    result = subprocess.run(
        cmd, cwd=project, capture_output=True, text=True, check=False
    )
    if result.stdout:
        click.echo(result.stdout.rstrip())
    if result.stderr:
        click.echo(result.stderr.rstrip())
    click.echo(f"[exit code: {result.returncode}]")
    if result.returncode != 0:
        msg = "The demo command failed. Inspect the output above."
        raise SystemExit(msg)


def _scenario_header(scenario: Scenario, project: Path) -> None:
    click.echo()
    click.echo("=" * 80)
    click.echo(f"{scenario.name}: {scenario.description}")
    click.echo(f"project: {project}")
    click.echo("=" * 80)


def _write_single_task_project(project: Path) -> None:
    _write(
        project / "task_example.py",
        """
        from pathlib import Path


        def task_example(produces=Path("out.txt")):
            produces.write_text("data")
        """,
    )


def _write_chain_project(project: Path) -> None:
    _write(
        project / "task_upstream.py",
        """
        from pathlib import Path


        def task_upstream(produces=Path("up.txt")):
            produces.write_text("up")
        """,
    )
    _write(
        project / "task_downstream.py",
        """
        from pathlib import Path


        def task_downstream(depends_on=Path("up.txt"), produces=Path("down.txt")):
            produces.write_text(depends_on.read_text() + "down")
        """,
    )


def _write_alpha_beta_project(project: Path) -> None:
    _write(
        project / "task_alpha.py",
        """
        from pathlib import Path


        def task_alpha(produces=Path("alpha.txt")):
            produces.write_text("alpha")
        """,
    )
    _write(
        project / "task_beta.py",
        """
        from pathlib import Path


        def task_beta(produces=Path("beta.txt")):
            produces.write_text("beta")
        """,
    )


def scenario_golden_path(project: Path) -> None:
    _write_single_task_project(project)

    _run(project)

    task = project / "task_example.py"
    task.write_text(task.read_text() + "\n# changed without rerunning\n")

    _run(project, "lock", "accept", "-k", "example", "--yes")
    _run(project)
    _run(project, "lock", "reset", "-k", "example", "--yes")
    _run(project)


def scenario_accept_ancestors(project: Path) -> None:
    _write_chain_project(project)

    _run(project)

    upstream = project / "task_upstream.py"
    downstream = project / "task_downstream.py"
    upstream.write_text(upstream.read_text() + "\n# changed upstream\n")
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    _run(project, "lock", "accept", "-k", "downstream", "--yes")
    _run(project)

    upstream.write_text(upstream.read_text() + "\n# changed upstream again\n")
    downstream.write_text(downstream.read_text() + "\n# changed downstream again\n")

    _run(project, "lock", "accept", "-k", "upstream", "--yes")
    _run(project)


def scenario_clean_subtractive(project: Path) -> None:
    _write_alpha_beta_project(project)

    _run(project)

    (project / "task_alpha.py").unlink()
    _write(
        project / "task_gamma.py",
        """
        from pathlib import Path


        def task_gamma(produces=Path("gamma.txt")):
            produces.write_text("gamma")
        """,
    )

    _run(project, "lock", "clean", "--yes")
    _run(project)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=[scenario.name for scenario in SCENARIOS] + ["all"],
        default="all",
        help="Select one scenario or run them all.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep temporary project directories instead of deleting them.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    selected = [
        scenario for scenario in SCENARIOS if args.scenario in ("all", scenario.name)
    ]

    for scenario in selected:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"pytask-{scenario.name}-"))
        _scenario_header(scenario, temp_dir)
        try:
            globals()[scenario.callback_name](temp_dir)
        finally:
            if args.keep:
                click.echo()
                click.echo(f"kept project at {temp_dir}")
            else:
                shutil.rmtree(temp_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
