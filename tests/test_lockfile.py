from __future__ import annotations

import textwrap

import pytest

from _pytask.lockfile import CURRENT_LOCKFILE_VERSION
from _pytask.lockfile import LockfileVersionError
from _pytask.lockfile import read_lockfile


def test_lockfile_upgrades_older_version(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text(
        textwrap.dedent(
            """
            lock-version = "0.9"
            task = []
            """
        ).strip()
        + "\n"
    )

    lockfile = read_lockfile(path)

    assert lockfile is not None
    assert lockfile.lock_version == CURRENT_LOCKFILE_VERSION


def test_lockfile_rejects_newer_version(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text(
        textwrap.dedent(
            """
            lock-version = "9.0"
            task = []
            """
        ).strip()
        + "\n"
    )

    with pytest.raises(LockfileVersionError):
        read_lockfile(path)
