"""Run docs commands with a temporary config containing the current version."""

from __future__ import annotations

import argparse
import importlib.metadata
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "serve"))
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args()

    config_path = Path("mkdocs.yml")
    with config_path.open(encoding="utf-8") as fh:
        config: dict[str, Any] = yaml.safe_load(fh)

    config.setdefault("extra", {})["version"] = importlib.metadata.version("pytask")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".yml", dir=".", delete=False
    ) as fh:
        yaml.safe_dump(config, fh, sort_keys=False)
        temporary_config_path = Path(fh.name)

    try:
        subprocess.run(
            [
                "zensical",
                parsed.command,
                "-f",
                str(temporary_config_path),
                *parsed.args,
            ],
            check=True,
        )
    finally:
        temporary_config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
