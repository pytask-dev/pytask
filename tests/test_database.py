from __future__ import annotations

import textwrap

import pytest
from _pytask.database_utils import create_database
from _pytask.database_utils import DatabaseSession
from _pytask.database_utils import State
from _pytask.path import hash_path
from pytask import cli
from pytask import ExitCode
from sqlalchemy.engine import make_url


@pytest.mark.end_to_end()
def test_existence_of_hashes_in_db(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write(depends_on, produces):
        produces.touch()
    """
    task_path = tmp_path.joinpath("task_module.py")
    task_path.write_text(textwrap.dedent(source))
    in_path = tmp_path.joinpath("in.txt")
    in_path.touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK

    create_database(
        make_url(
            "sqlite:///" + tmp_path.joinpath(".pytask", "pytask.sqlite3").as_posix()
        )
    )

    with DatabaseSession() as session:
        task_id = task_path.as_posix() + "::task_write"
        out_path = tmp_path.joinpath("out.txt")

        for id_, path in (
            (task_id, task_path),
            (in_path.as_posix(), in_path),
            (out_path.as_posix(), out_path),
        ):
            hash_ = session.get(State, (task_id, id_)).hash_
            assert hash_ == hash_path(path, path.stat().st_mtime)


@pytest.mark.end_to_end()
def test_rename_database_w_config(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\ndatabase_url='sqlite:///.db.sqlite'"
    )
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()


@pytest.mark.end_to_end()
def test_rename_database_w_cli(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    result = runner.invoke(
        cli,
        ["--database-url", "sqlite:///.db.sqlite", tmp_path.as_posix()],
    )
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()
