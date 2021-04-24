import textwrap

import pytest
from _pytask.database import create_database
from _pytask.profiling import Runtime
from pony import orm
from pytask import main


@pytest.mark.end_to_end
def test_duration_is_stored_in_task(tmp_path):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.tasks) == 1
    task = session.tasks[0]
    duration = task.attributes["duration"]
    assert duration[1] - duration[0] > 2

    with orm.db_session:
        create_database(
            "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
        )

        task_name = tmp_path.joinpath("task_example.py").as_posix() + "::task_example"

        runtime = Runtime[task_name]
        assert runtime.duration > 2
