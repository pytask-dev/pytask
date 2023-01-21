from __future__ import annotations

import textwrap

import pytest
from _pytask.database_utils import create_database
from _pytask.database_utils import State
from pony import orm
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end
def test_existence_of_hashes_in_db(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write(produces):
        produces.touch()
    """
    task_path = tmp_path.joinpath("task_module.py")
    task_path.write_text(textwrap.dedent(source))
    in_path = tmp_path.joinpath("in.txt")
    in_path.touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK

    with orm.db_session:

        create_database(
            "sqlite",
            tmp_path.joinpath(".pytask.sqlite3").as_posix(),
            create_db=True,
            create_tables=False,
        )

        task_id = task_path.as_posix() + "::task_write"
        out_path = tmp_path.joinpath("out.txt")

        for id_, path in (
            (task_id, task_path),
            (in_path.as_posix(), in_path),
            (out_path.as_posix(), out_path),
        ):
            state = State[task_id, id_].state
            assert float(state) == path.stat().st_mtime


@pytest.mark.end_to_end
def test_rename_database_w_config(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\ndatabase_filename='.db.sqlite3'"
    )
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    tmp_path.joinpath(".db.sqlite3").exists()


@pytest.mark.end_to_end
def test_rename_database_w_cli(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    result = runner.invoke(
        cli, ["--database-filename", ".db.sqlite3", tmp_path.as_posix()]
    )
    assert result.exit_code == ExitCode.OK
    tmp_path.joinpath(".db.sqlite3").exists()
