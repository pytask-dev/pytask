import os
import textwrap

from _pytask.database import create_database
from _pytask.database import State
from pony import orm
from pytask import cli


def test_existence_of_hashes_in_db(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(produces):
        produces.touch()
    """
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))
    in_path = tmp_path.joinpath("in.txt")
    in_path.touch()

    os.chdir(tmp_path)
    result = runner.invoke(cli)

    assert result.exit_code == 0

    orm.db_session.__enter__()

    create_database(
        "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
    )

    task_id = task_path.as_posix() + "::task_dummy"
    out_path = tmp_path.joinpath("out.txt")

    for id_, path in [
        (task_id, task_path),
        (in_path.as_posix(), in_path),
        (out_path.as_posix(), out_path),
    ]:
        state = State[task_id, id_].state
        assert float(state) == path.stat().st_mtime

    orm.db_session.__exit__()
