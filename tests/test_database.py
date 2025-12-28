from __future__ import annotations

import textwrap

from sqlalchemy.engine import make_url

from pytask import DatabaseSession
from pytask import ExitCode
from pytask import State
from pytask import build
from pytask import cli
from pytask import create_database
from pytask.path import hash_path


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
        make_url(  # type: ignore[arg-type]
            "sqlite:///" + tmp_path.joinpath(".pytask", "pytask.sqlite3").as_posix()
        )
    )

    with DatabaseSession() as db_session:
        task_id = session.tasks[0].signature
        out_path = tmp_path.joinpath("out.txt")
        depends_on = session.tasks[0].depends_on
        produces = session.tasks[0].produces
        assert depends_on is not None
        assert produces is not None
        in_id = depends_on["path"].signature  # type: ignore[union-attr]
        out_id = produces["produces"].signature  # type: ignore[union-attr]

        for id_, path in (
            (task_id, task_path),
            (in_id, in_path),
            (out_id, out_path),
        ):
            state = db_session.get(State, (task_id, id_))
            assert state is not None
            hash_ = state.hash_
            assert hash_ == hash_path(path, path.stat().st_mtime)


def test_rename_database_w_config(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\ndatabase_url='sqlite:///.db.sqlite'"
    )
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()


def test_rename_database_w_cli(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    result = runner.invoke(
        cli,
        ["--database-url", "sqlite:///.db.sqlite", tmp_path.as_posix()],
    )
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()
