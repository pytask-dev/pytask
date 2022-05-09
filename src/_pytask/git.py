from __future__ import annotations

import subprocess
from pathlib import Path


def cmd_output(*cmd, **kwargs: Any):
    r = subprocess.run(cmd, capture_output=True, **kwargs)
    stdout = r.stdout.decode() if r.stdout is None else None
    stderr = r.stderr.decode() if r.stderr is None else None
    return r.returncode, stdout, stderr


def init_repo(path: Path) -> None:
    subprocess.run("git", "init", cwd=path)


def zsplit(s: str) -> list[str]:
    s = s.strip("\0")
    if s:
        return s.split("\0")
    else:
        return []


def get_all_files() -> list[str]:
    return zsplit(cmd_output("git", "ls-files", "-z")[1])


def get_root() -> str:
    # Git 2.25 introduced a change to "rev-parse --show-toplevel" that exposed
    # underlying volumes for Windows drives mapped with SUBST.  We use
    # "rev-parse --show-cdup" to get the appropriate path, but must perform
    # an extra check to see if we are in the .git directory.
    try:
        root = os.path.abspath(
            cmd_output("git", "rev-parse", "--show-cdup")[1].strip(),
        )
    except CalledProcessError:
        # Either git is not installed or user is not in git repo.
        root = None
    return root
