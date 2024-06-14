from __future__ import annotations

import textwrap

import pytest
from pytask import DatabaseSession
from pytask import ExitCode
from pytask import State
from pytask import build
from pytask import create_database
from pytask.path import hash_path
from sqlalchemy.engine import make_url


@pytest.mark.end_to_end()
def test_existence_of_hashes_in_db(tmp_path):
    """Modification dates of input and output files are stored in database."""
    source = """
    from pathlib import Path

    def task_write(path=Path("in.txt"), produces=Path("out.txt")):
        produces.touch()
    """
    task_path = tmp_path.joinpath("task_module.py")
    task_path.write_text(textwrap.dedent(source))
    in_path = tmp_path.joinpath("in.txt")
    in_path.touch()

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK

    create_database(
        make_url(
            "sqlite:///" + tmp_path.joinpath(".pytask", "pytask.sqlite3").as_posix()
        )
    )

    with DatabaseSession() as db_session:
        task_id = session.tasks[0].signature
        out_path = tmp_path.joinpath("out.txt")
        in_id = session.tasks[0].depends_on["path"].signature
        out_id = session.tasks[0].produces["produces"].signature

        for id_, path in (
            (task_id, task_path),
            (in_id, in_path),
            (out_id, out_path),
        ):
            hash_ = db_session.get(State, (task_id, id_)).hash_
            assert hash_ == hash_path(path, path.stat().st_mtime)
