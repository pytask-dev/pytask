import itertools
import textwrap

import pytask
import pytest
from pytask.main import pytask_main
from pytask.mark.structures import Mark
from pytask.parametrize import _parse_arg_names
from pytask.parametrize import _parse_parametrize_markers
from pytask.parametrize import pytask_generate_tasks
from pytask.pluginmanager import get_plugin_manager


class DummySession:
    pass


@pytest.fixture(scope="module")
def session():
    pm = get_plugin_manager()
    pm.register(pytask.parametrize)

    session = DummySession()
    session.hook = pm.hook

    return session


@pytest.mark.integration
def test_pytask_generate_tasks_0(session):
    @pytask.mark.parametrize("i", range(2))
    def func(i):
        pass

    names_and_objs = pytask_generate_tasks(session, "func", func)

    assert [i[0] for i in names_and_objs] == ["func[i0]", "func[i1]"]
    assert names_and_objs[0][1].keywords["i"] == 0
    assert names_and_objs[1][1].keywords["i"] == 1


@pytest.mark.integration
def test_pytask_generate_tasks_1(session):
    @pytask.mark.parametrize("j", range(2))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j):
        pass

    names_and_objs = pytask_generate_tasks(session, "func", func)

    for (name, func), values in zip(
        names_and_objs, itertools.product(range(2), range(2))
    ):
        assert name == f"func[i{values[0]}-j{values[1]}]"
        assert func.keywords["i"] == values[0]
        assert func.keywords["j"] == values[1]


@pytest.mark.integration
def test_pytask_generate_tasks_2(session):
    @pytask.mark.parametrize("j, k", itertools.product(range(2), range(2)))
    @pytask.mark.parametrize("i", range(2))
    def func(i, j, k):
        pass

    names_and_objs = pytask_generate_tasks(session, "func", func)

    for (name, func), arg_names, values in zip(
        names_and_objs,
        itertools.product(range(2), range(4)),
        itertools.product(range(2), range(2), range(2)),
    ):
        assert name == f"func[i{arg_names[0]}-j{arg_names[1]}-k{arg_names[1]}]"
        assert func.keywords["i"] == values[0]
        assert func.keywords["j"] == values[1]
        assert func.keywords["k"] == values[2]


@pytest.mark.integration
def test_pytask_parametrize_missing_func_args(session):
    """Missing function args with parametrized tasks raise an error during execution."""

    @pytask.mark.parametrize("i", range(2))
    def func():
        pass

    names_and_functions = pytask_generate_tasks(session, "func", func)
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
            [[("i0",), ("i1",)], [("j0",), ("j1",)]],
            [[(0,), (1,)], [(0,), (1,)]],
        ),
        (
            [Mark("parametrize", ("i", range(3)), {})],
            [("i",)],
            [[("i0",), ("i1",), ("i2",)]],
            [[(0,), (1,), (2,)]],
        ),
    ],
)
def test_parse_parametrize_markers(
    markers, exp_base_arg_names, exp_arg_names, exp_arg_values
):
    base_arg_names, arg_names, arg_values = _parse_parametrize_markers(markers)

    assert base_arg_names == exp_base_arg_names
    assert arg_names == exp_arg_names
    assert arg_values == exp_arg_values


@pytest.mark.end_to_end
def test_parametrizing_tasks(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.parametrize('i, produces', [(1, Path("1.txt")), (2, Path("2.txt"))])
    def task_write_numbers_to_file(produces, i):
        produces.write_text(str(i))
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = pytask_main({"paths": tmp_path})

    assert session.exit_code == 0
    for i in range(1, 3):
        assert tmp_path.joinpath(f"{i}.txt").read_text() == str(i)


@pytest.mark.end_to_end
def test_parametrizing_dependencies_and_targets(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.parametrize('i, produces', [(1, Path("1.txt")), (2, Path("2.txt"))])
    def task_save_numbers(i, produces):
        produces.write_text(str(i))


    @pytask.mark.parametrize("depends_on, produces", [
        (Path("1.txt"), Path("1_out.txt")), (Path("2.txt"), Path("2_out.txt"))
    ])
    def task_save_numbers_again(depends_on, produces):
        produces.write_text(depends_on.read_text())

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = pytask_main({"paths": tmp_path})

    assert session.exit_code == 0
