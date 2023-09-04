"""Contains all functions related to git."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike


def is_git_installed() -> bool:
    """Check if git is installed."""
    return shutil.which("git") is not None


def cmd_output(*cmd: str, **kwargs: Any) -> tuple[int, str, str]:
    """Execute a command and capture the output."""
    r = subprocess.run(cmd, capture_output=True, check=False, **kwargs)
    stdout = r.stdout.decode() if r.stdout is not None else None
    stderr = r.stderr.decode() if r.stderr is not None else None
    return r.returncode, stdout, stderr


def init_repo(path: Path) -> None:
    """Initialize a git repository."""
    subprocess.run(("git", "init"), check=False, cwd=path)


def zsplit(s: str) -> list[str]:
    """Split string which uses the NUL character as a separator."""
    s = s.strip("\0")
    if s:
        return s.split("\0")
    return []


def get_all_files(cwd: PathLike[str] | None = None) -> list[Path]:
    """Get all files tracked by git - even new, staged files."""
    str_paths = zsplit(cmd_output("git", "ls-files", "-z", cwd=cwd)[1])
    return [Path(x) for x in str_paths]


def get_root(cwd: PathLike[str] | None) -> Path | None:
    """Get the root path of a git repository.

    Git 2.25 introduced a change to ``rev-parse --show-toplevel`` that exposed
    underlying volumes for Windows drives mapped with ``SUBST``.  We use ``rev-parse
    --show-cdup`` to get the appropriate path.

    """
    try:
        _, stdout, _ = cmd_output("git", "rev-parse", "--show-cdup", cwd=cwd)
        root = Path(cwd) / stdout.strip()
    except subprocess.CalledProcessError:
        # User is not in git repo.
        root = None
    return root
