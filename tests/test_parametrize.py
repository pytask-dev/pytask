from __future__ import annotations

import itertools
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from typing import NamedTuple

import _pytask.parametrize
import pytask
import pytest
from _pytask.parametrize import _check_if_n_arg_names_matches_n_arg_values
from _pytask.parametrize import _parse_arg_names
from _pytask.parametrize import _parse_arg_values
from _pytask.parametrize import _parse_parametrize_markers
from _pytask.parametrize import pytask_parametrize_task
from _pytask.pluginmanager import get_plugin_manager
from pytask import cli
from pytask import ExitCode
from pytask import main
from pytask import Mark
from pytask import Session


@pytest.fixture(scope="module")
def session():
    pm = get_plugin_manager()
    pm.register(_pytask.parametrize)
    session = Session(hook=pm.hook)
    return session


@pytest.mark.integration
def test_pytask_generate_tasks_0(session):
    @pytask.mark.parametrize("i", range(2))
    def func(i):  # noqa: ARG001, pragma: no cover
        pass

    names_and_objs = pytask_parametrize_task(session, "func", func)

    assert [i[0] for i in names_and_objs] == ["func[0]", "func[1]"]
    assert names_and_objs[0][1].pytask_meta.kwargs["i"] == 0
    assert names_and_objs[1][1].pytask_meta.kwargs["i"] == 1


@pytest.mark.integration
@pytest.mark.xfail(strict=True, reason="Cartesian task product is disabled.")
def test_pytask_generate_tasks_1(session):
    @pytask.mark.parametrize("j", range(2))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j):  # noqa: ARG001, pragma: no cover
        pass

    pytask_parametrize_task(session, "func", func)


@pytest.mark.integration
@pytest.mark.xfail(strict=True, reason="Cartesian task product is disabled.")
def test_pytask_generate_tasks_2(session):
    @pytask.mark.parametrize("j, k", itertools.product(range(2), range(2)))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j, k):  # noqa: ARG001, pragma: no cover
        pass

    pytask_parametrize_task(session, "func", func)


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_names, expected",
    [
        ("i", ("i",)),
        ("i,j", ("i", "j")),
        ("i, j", ("i", "j")),
        (("i", "j"), ("i", "j")),
        (["i", "j"], ("i", "j")),
    ],
)
def test_parse_arg_names(arg_names, expected):
    parsed_arg_names = _parse_arg_names(arg_names)
    assert parsed_arg_names == expected


class TaskArguments(NamedTuple):
    a: int
    b: int


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_values, has_single_arg, expected",
    [
        (["a", "b", "c"], True, [("a",), ("b",), ("c",)]),
        ([(0, 0), (0, 1), (1, 0)], False, [(0, 0), (0, 1), (1, 0)]),
        ([[0, 0], [0, 1], [1, 0]], False, [(0, 0), (0, 1), (1, 0)]),
        ({"a": 0, "b": 1}, False, [("a",), ("b",)]),
        ([{"a": 0, "b": 1}], True, [({"a": 0, "b": 1},)]),
        ([TaskArguments(1, 2)], False, [(1, 2)]),
        ([TaskArguments(a=1, b=2)], False, [(1, 2)]),
        ([TaskArguments(b=2, a=1)], False, [(1, 2)]),
    ],
)
def test_parse_arg_values(arg_values, has_single_arg, expected):
    parsed_arg_values = _parse_arg_values(arg_values, has_single_arg)
    assert parsed_arg_values == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_names, expectation",
    [
        ("i", does_not_raise()),
        ("i, j", does_not_raise()),
        (("i", "j"), does_not_raise()),
        (["i", "j"], does_not_raise()),
        (range(1, 2), pytest.raises(TypeError)),
        ({"i": None, "j": None}, pytest.raises(TypeError)),
        ({"i", "j"}, pytest.raises(TypeError)),
    ],
)
def test_parse_argnames_raise_error(arg_names, expectation):
    with expectation:
        _parse_arg_names(arg_names)


@pytest.mark.integration
@pytest.mark.parametrize(
    "markers, exp_base_arg_names, exp_arg_names, exp_arg_values",
    [
        (
            [
                Mark("parametrize", ("i", range(2)), {}),
                Mark("parametrize", ("j", range(2)), {}),
            ],
            [("i",), ("j",)],
            [[("0",), ("1",)], [("0",), ("1",)]],
            [[(0,), (1,)], [(0,), (1,)]],
        ),
        (
            [Mark("parametrize", ("i", range(3)), {})],
            [("i",)],
            [[("0",), ("1",), ("2",)]],
            [[(0,), (1,), (2,)]],
        ),
    ],
)
def test_parse_parametrize_markers(
    markers, exp_base_arg_names, exp_arg_names, exp_arg_values
):
    base_arg_names, arg_names, arg_values = _parse_parametrize_markers(markers, "task_")

    assert base_arg_names == exp_base_arg_names
    assert arg_names == exp_arg_names
    assert arg_values == exp_arg_values


@pytest.mark.end_to_end
def test_parametrizing_tasks(tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i, produces', [(1, "1.txt"), (2, "2.txt")])
    def task_write_numbers_to_file(produces, i):
        produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    for i in range(1, 3):
        assert tmp_path.joinpath(f"{i}.txt").read_text() == str(i)


@pytest.mark.end_to_end
def test_parametrizing_dependencies_and_targets(tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i, produces', [(1, "1.txt"), (2, "2.txt")])
    def task_save_numbers(i, produces):
        produces.write_text(str(i))

    @pytask.mark.parametrize("depends_on, produces", [
        ("1.txt", "1_out.txt"), ("2.txt", "2_out.txt")
    ])
    def task_save_numbers_again(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK


@pytest.mark.end_to_end
def test_parametrize_iterator(tmp_path):
    """`parametrize` should work with generators."""
    source = """
    import pytask
    def gen():
        yield 1
        yield 2
        yield 3
    @pytask.mark.parametrize('a', gen())
    def task_func(a):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    session = main({"paths": tmp_path})
    assert session.exit_code == ExitCode.OK
    assert len(session.execution_reports) == 3


@pytest.mark.end_to_end
def test_raise_error_if_function_does_not_use_parametrized_arguments(tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i', range(2))
    def task_func():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.FAILED
    assert isinstance(session.execution_reports[0].exc_info[1], TypeError)
    assert isinstance(session.execution_reports[1].exc_info[1], TypeError)


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "arg_values, ids",
    [
        (range(2), ["first_trial", "second_trial"]),
        ([True, False], ["first_trial", "second_trial"]),
    ],
)
def test_parametrize_w_ids(tmp_path, arg_values, ids):
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            f"""
            import pytask

            @pytask.mark.parametrize('i', {arg_values}, ids={ids})
            def task_func(i):
                pass
            """
        )
    )
    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    for task, id_ in zip(session.tasks, ids):
        assert id_ in task.name


@pytest.mark.end_to_end
def test_two_parametrize_w_ids(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i', range(2), ids=["2.1", "2.2"])
    @pytask.mark.parametrize('j', range(2), ids=["1.1", "1.2"])
    def task_func(i, j):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "You cannot apply @pytask.mark.parametrize multiple" in result.output


@pytest.mark.end_to_end
@pytest.mark.parametrize("ids", [["a"], list("abc"), ((1,), (2,)), ({0}, {1})])
def test_raise_error_for_irregular_ids(tmp_path, ids):
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            f"""
            import pytask

            @pytask.mark.parametrize('i', range(2), ids={ids})
            def task_func():
                pass
            """
        )
    )
    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert isinstance(session.collection_reports[0].exc_info[1], ValueError)


@pytest.mark.end_to_end
def test_raise_error_if_parametrization_produces_non_unique_tasks(tmp_path):
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            """
            import pytask

            @pytask.mark.parametrize('i', [0, 0])
            def task_func(i):
                pass
            """
        )
    )
    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert isinstance(session.collection_reports[0].exc_info[1], ValueError)


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "arg_names, arg_values, content",
    [
        (
            ("i", "j"),
            [1, 2, 3],
            [
                "ValueError",
                "with 2 'arg_names', ('i', 'j'),",
                "'arg_values' is 1.",
                "parametrization no. 0:",
                "(1,)",
            ],
        ),
        (
            ("i", "j"),
            [(1, 2, 3)],
            [
                "ValueError",
                "with 2 'arg_names', ('i', 'j'),",
                "'arg_values' is 3.",
                "parametrization no. 0:",
                "(1, 2, 3)",
            ],
        ),
        (
            ("i", "j"),
            [(1, 2), (1, 2, 3)],
            [
                "ValueError",
                "with 2 'arg_names', ('i', 'j'),",
                "'arg_values' is 2 or 3.",
                "parametrization no. 1:",
                "(1, 2, 3)",
            ],
        ),
    ],
)
def test_wrong_number_of_names_and_wrong_number_of_arguments(
    tmp_path, runner, arg_names, arg_values, content
):
    source = f"""
    import pytask

    @pytask.mark.parametrize({arg_names}, {arg_values})
    def task_func():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    for c in content:
        assert c in result.output


@pytest.mark.end_to_end
def test_generators_are_removed_from_depends_on_produces(tmp_path):
    source = """
    from pathlib import Path
    import pytask

    @pytask.mark.parametrize("produces", [
        ((x for x in ["out.txt", "out_2.txt"]),),
        ["in.txt"],
    ])
    def task_example(produces):
        produces = {0: produces} if isinstance(produces, Path) else produces
        for p in produces.values():
            p.write_text("hihi")
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert session.exit_code == ExitCode.OK
    assert session.tasks[0].function.pytask_meta.markers == []


@pytest.mark.end_to_end
def test_parametrizing_tasks_with_namedtuples(runner, tmp_path):
    source = """
    from typing import NamedTuple
    import pytask
    from pathlib import Path


    class Task(NamedTuple):
        i: int
        produces: Path


    @pytask.mark.parametrize('i, produces', [
        Task(i=1, produces="1.txt"), Task(produces="2.txt", i=2),
    ])
    def task_write_numbers_to_file(produces, i):
        produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    for i in range(1, 3):
        assert tmp_path.joinpath(f"{i}.txt").read_text() == str(i)


@pytest.mark.end_to_end
def test_parametrization_with_different_n_of_arg_names_and_arg_values(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i, produces', [(1, "1.txt"), (2, 3, "2.txt")])
    def task_write_numbers_to_file(produces, i):
        produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Task 'task_write_numbers_to_file' is parametrized with 2" in result.output


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_names, arg_values, name, expectation",
    [
        pytest.param(
            ("a",),
            [(1,), (2,)],
            "task_name",
            does_not_raise(),
            id="normal one argument parametrization",
        ),
        pytest.param(
            ("a", "b"),
            [(1, 2), (3, 4)],
            "task_name",
            does_not_raise(),
            id="normal two argument argument parametrization",
        ),
        pytest.param(
            ("a",),
            [(1, 2), (2,)],
            "task_name",
            pytest.raises(ValueError, match="Task 'task_name' is parametrized with 1"),
            id="error with one argument parametrization",
        ),
        pytest.param(
            ("a", "b"),
            [(1, 2), (3, 4, 5)],
            "task_name",
            pytest.raises(ValueError, match="Task 'task_name' is parametrized with 2"),
            id="error with two argument argument parametrization",
        ),
    ],
)
def test_check_if_n_arg_names_matches_n_arg_values(
    arg_names, arg_values, name, expectation
):
    with expectation:
        _check_if_n_arg_names_matches_n_arg_values(arg_names, arg_values, name)


@pytest.mark.end_to_end
def test_parametrize_with_single_dict(tmp_path):
    source = """
    import pytask

    @pytask.mark.parametrize('i', [{"a": 1}, {"a": 1.0}])
    def task_write_numbers_to_file(i):
        assert i["a"] == 1
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
