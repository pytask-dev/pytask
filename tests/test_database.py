from __future__ import annotations

import os
import textwrap

import pytest
from _pytask.database import create_database
from _pytask.database import State
from _pytask.outcomes import ExitCode
from pony import orm
from pytask import cli


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

    os.chdir(tmp_path)
    result = runner.invoke(cli)

    assert result.exit_code == ExitCode.OK

    with orm.db_session:

        create_database(
            "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
        )

        task_id = task_path.as_posix() + "::task_write"
        out_path = tmp_path.joinpath("out.txt")

        for id_, path in [
            (task_id, task_path),
            (in_path.as_posix(), in_path),
            (out_path.as_posix(), out_path),
        ]:
            state = State[task_id, id_].state
            assert float(state) == path.stat().st_mtime
