import textwrap

import pytest
from _pytask.database import create_database
from _pytask.database import State
from _pytask.outcomes import Persisted
from _pytask.outcomes import SkippedUnchanged
from _pytask.persist import pytask_execute_task_process_report
from pony import orm
from pytask import main


class DummyClass:
    pass


@pytest.mark.end_to_end
def test_persist_marker_is_set(tmp_path):
    session = main({"paths": tmp_path})
    assert "persist" in session.config["markers"]


@pytest.mark.end_to_end
def test_multiple_runs_with_persist(tmp_path):
    """Perform multiple consecutive runs and check intermediate outcomes with persist.

    1. The product is missing which should result in a normal execution of the task.
    2. Change the product, check that run is successful and state in database has
       changed.
    3. Run the task another time. Now, the task is skipped successfully.

    """
    source = """
    import pytask

    @pytask.mark.persist
    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("I'm not the reason you care.")

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].success
    assert session.execution_reports[0].exc_info is None
    assert tmp_path.joinpath("out.txt").exists()

    tmp_path.joinpath("out.txt").write_text("Never again in despair.")

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].success
    assert isinstance(session.execution_reports[0].exc_info[1], Persisted)

    with orm.db_session:
        create_database(
            "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
        )
        task_id = tmp_path.joinpath("task_dummy.py").as_posix() + "::task_dummy"
        node_id = tmp_path.joinpath("out.txt").as_posix()

        state = State[task_id, node_id].state
        assert float(state) == tmp_path.joinpath("out.txt").stat().st_mtime

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].success
    assert isinstance(session.execution_reports[0].exc_info[1], SkippedUnchanged)


@pytest.mark.end_to_end
def test_migrating_a_whole_task_with_persist(tmp_path):
    source = """
    import pytask

    @pytask.mark.persist
    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    for name in ["in.txt", "out.txt"]:
        tmp_path.joinpath(name).write_text(
            "They say oh my god I see the way you shine."
        )

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].success
    assert isinstance(session.execution_reports[0].exc_info[1], Persisted)


@pytest.mark.unit
@pytest.mark.parametrize(
    "exc_info, expected",
    [
        (None, None),
        ((None, None, None), None),
        ((None, Persisted(), None), True),
    ],
)
def test_pytask_execute_task_process_report(exc_info, expected):
    report = DummyClass()
    report.exc_info = exc_info
    result = pytask_execute_task_process_report(report)

    if expected:
        assert report.success
    else:
        assert result is None
