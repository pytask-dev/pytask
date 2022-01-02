import itertools
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import _pytask.parametrize
import pytask
import pytest
from _pytask.mark import Mark
from _pytask.parametrize import _arg_value_to_id_component
from _pytask.parametrize import _parse_arg_names
from _pytask.parametrize import _parse_parametrize_markers
from _pytask.parametrize import pytask_parametrize_task
from _pytask.pluginmanager import get_plugin_manager
from pytask import cli
from pytask import main


class DummySession:
    pass


@pytest.fixture(scope="module")
def session():
    pm = get_plugin_manager()
    pm.register(_pytask.parametrize)

    session = DummySession()
    session.hook = pm.hook

    return session


@pytest.mark.integration
def test_pytask_generate_tasks_0(session):
    @pytask.mark.parametrize("i", range(2))
    def func(i):  # noqa: U100
        pass

    names_and_objs = pytask_parametrize_task(session, "func", func)

    assert [i[0] for i in names_and_objs] == ["func[0]", "func[1]"]
    assert names_and_objs[0][1].keywords["i"] == 0
    assert names_and_objs[1][1].keywords["i"] == 1


@pytest.mark.integration
@pytest.mark.xfail(strict=True, reason="Cartesian task product is disabled.")
def test_pytask_generate_tasks_1(session):
    @pytask.mark.parametrize("j", range(2))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j):  # noqa: U100
        pass

    names_and_objs = pytask_parametrize_task(session, "func", func)

    for (name, func), values in zip(
        names_and_objs, itertools.product(range(2), range(2))
    ):
        assert name == f"func[{values[0]}-{values[1]}]"
        assert func.keywords["i"] == values[0]
        assert func.keywords["j"] == values[1]


@pytest.mark.integration
@pytest.mark.xfail(strict=True, reason="Cartesian task product is disabled.")
def test_pytask_generate_tasks_2(session):
    @pytask.mark.parametrize("j, k", itertools.product(range(2), range(2)))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j, k):  # noqa: U100
        pass

    names_and_objs = pytask_parametrize_task(session, "func", func)

    for (name, func), values in zip(
        names_and_objs,
        [(i, j, k) for i in range(2) for j in range(2) for k in range(2)],
    ):
        assert name == f"func[{values[0]}-{values[1]}-{values[2]}]"
        assert func.keywords["i"] == values[0]
        assert func.keywords["j"] == values[1]
        assert func.keywords["k"] == values[2]


@pytest.mark.integration
def test_pytask_parametrize_missing_func_args(session):
    """Missing function args with parametrized tasks raise an error during execution."""

    @pytask.mark.parametrize("i", range(2))
    def func():
        pass

    names_and_functions = pytask_parametrize_task(session, "func", func)
    for _, func in names_and_functions:
        with pytest.raises(TypeError):
            func()


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
def test_parse_argnames(arg_names, expected):
    parsed_argnames = _parse_arg_names(arg_names)
    assert parsed_argnames == expected


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

    assert session.exit_code == 0
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

    assert session.exit_code == 0


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
    assert session.exit_code == 0
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

    assert session.exit_code == 1
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

    assert session.exit_code == 0
    for task, id_ in zip(session.tasks, ids):
        assert id_ in task.name


@pytest.mark.end_to_end
@pytest.mark.xfail(strict=True, reason="Cartesian task product is disabled.")
def test_two_parametrize_w_ids(tmp_path):
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            """
            import pytask

            @pytask.mark.parametrize('i', range(2), ids=["2.1", "2.2"])
            @pytask.mark.parametrize('j', range(2), ids=["1.1", "1.2"])
            def task_func(i, j):
                pass
            """
        )
    )
    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.tasks) == 4
    for task, id_ in zip(
        session.tasks, ["[1.1-2.1]", "[1.1-2.2]", "[1.2-2.1]", "[1.2-2.2]"]
    ):
        assert id_ in task.name


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

    assert session.exit_code == 3
    assert isinstance(session.collection_reports[0].exc_info[1], ValueError)


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_name, arg_value, i, id_func, expected",
    [
        ("arg", 1, 0, None, "1"),
        ("arg", True, 0, None, "True"),
        ("arg", False, 0, None, "False"),
        ("arg", 1.0, 0, None, "1.0"),
        ("arg", None, 0, None, "arg0"),
        ("arg", (1,), 0, None, "arg0"),
        ("arg", [1], 0, None, "arg0"),
        ("arg", {1, 2}, 0, None, "arg0"),
        ("arg", 1, 0, lambda x: bool(x), "True"),
        ("arg", 1, 1, lambda x: None, "1"),
        ("arg", [1], 2, lambda x: None, "arg2"),
    ],
)
def test_arg_value_to_id_component(arg_name, arg_value, i, id_func, expected):
    result = _arg_value_to_id_component(arg_name, arg_value, i, id_func)
    assert result == expected


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

    assert session.exit_code == 3
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

    assert result.exit_code == 3
    for c in content:
        assert c in result.output
