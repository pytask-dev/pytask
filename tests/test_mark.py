import sys
import textwrap

import pytask
import pytest
from pytask.main import pytask_main
from pytask.mark_ import MarkGenerator


@pytest.mark.unit
@pytest.mark.parametrize("attribute", ["hookimpl", "mark"])
def test_mark_exists_in_pytask_namespace(attribute):
    assert attribute in sys.modules["pytask"].__all__


@pytest.mark.unit
def test_pytask_mark_notcallable() -> None:
    mark = MarkGenerator()
    with pytest.raises(TypeError):
        mark()


@pytest.mark.unit
@pytest.mark.filterwarnings("ignore:Unknown pytask.mark.foo")
def test_mark_with_param():
    def some_function(abc):
        pass

    class SomeClass:
        pass

    assert pytask.mark.foo(some_function) is some_function
    marked_with_args = pytask.mark.foo.with_args(some_function)
    assert marked_with_args is not some_function

    assert pytask.mark.foo(SomeClass) is SomeClass
    assert pytask.mark.foo.with_args(SomeClass) is not SomeClass


@pytest.mark.unit
def test_pytask_mark_name_starts_with_underscore():
    mark = MarkGenerator()
    with pytest.raises(AttributeError):
        mark._some_name


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_ini_markers(tmp_path, config_name):
    tmp_path.joinpath(config_name).write_text(
        textwrap.dedent(
            """
            [pytask]
            markers =
                a1: this is a webtest marker
                a2: this is a smoke marker
            """
        )
    )

    session = pytask_main({"paths": tmp_path})

    assert session.exit_code == 0
    assert "a1" in session.config["markers"]
    assert "a2" in session.config["markers"]
