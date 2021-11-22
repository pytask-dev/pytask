import sys
import types
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.compat import _MINIMUM_VERSIONS
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency


@pytest.mark.parametrize(
    "name, extra, errors, caller, expectation, expected",
    [
        pytest.param(
            "python",
            "",
            "raise",
            "pytask",
            does_not_raise(),
            True,
            id="program exists",
        ),
        pytest.param(
            "unknown_program",
            "",
            "raise",
            "pytask",
            pytest.raises(RuntimeError, match="pytask requires missing"),
            None,
            id="program does not exist and error raised",
        ),
        pytest.param(
            "unknown_program",
            "",
            "warn",
            "pytask",
            pytest.warns(UserWarning, match="pytask requires missing"),
            False,
            id="program does not exist and warning",
        ),
        pytest.param(
            "unknown_program",
            "extra included",
            "warn",
            "pytask",
            pytest.warns(UserWarning, match="extra included"),
            False,
            id="program does not exist and warning and extra",
        ),
        pytest.param(
            "unknown_program",
            "extra included",
            "ignore",
            "pytask",
            does_not_raise(),
            False,
            id="program does not exist and ignore and extra",
        ),
        pytest.param(
            None,
            "",
            "unknown_errors",
            "pytask",
            pytest.raises(ValueError, match="'errors' must be one of"),
            None,
            id="unknown errors",
        ),
    ],
)
def test_check_for_optional_program(name, extra, errors, caller, expectation, expected):
    with expectation:
        program_exists = check_for_optional_program(name, extra, errors, caller)
        assert program_exists is expected


def test_import_optional():
    match = "pytask requires .*notapackage.* pip .* conda .* 'notapackage'"
    with pytest.raises(ImportError, match=match) as exc_info:
        import_optional_dependency("notapackage")
    # The original exception should be there as context:
    assert isinstance(exc_info.value.__context__, ImportError)

    result = import_optional_dependency("notapackage", errors="ignore")
    assert result is None


def test_pony_version_fallback():
    pytest.importorskip("pony")
    import_optional_dependency("pony")


def test_bad_version(monkeypatch):
    name = "fakemodule"
    module = types.ModuleType(name)
    module.__version__ = "0.9.0"
    sys.modules[name] = module
    monkeypatch.setitem(_MINIMUM_VERSIONS, name, "1.0.0")

    match = "pytask requires .*1.0.0.* of .fakemodule.*'0.9.0'"
    with pytest.raises(ImportError, match=match):
        import_optional_dependency("fakemodule")

    # Test min_version parameter
    result = import_optional_dependency("fakemodule", min_version="0.8")
    assert result is module

    with pytest.warns(UserWarning):
        result = import_optional_dependency("fakemodule", errors="warn")
    assert result is None

    module.__version__ = "1.0.0"  # exact match is OK
    result = import_optional_dependency("fakemodule")
    assert result is module


def test_submodule(monkeypatch):
    # Create a fake module with a submodule
    name = "fakemodule"
    module = types.ModuleType(name)
    module.__version__ = "0.9.0"
    sys.modules[name] = module
    sub_name = "submodule"
    submodule = types.ModuleType(sub_name)
    setattr(module, sub_name, submodule)
    sys.modules[f"{name}.{sub_name}"] = submodule
    monkeypatch.setitem(_MINIMUM_VERSIONS, name, "1.0.0")

    match = "pytask requires .*1.0.0.* of .fakemodule.*'0.9.0'"
    with pytest.raises(ImportError, match=match):
        import_optional_dependency("fakemodule.submodule")

    with pytest.warns(UserWarning):
        result = import_optional_dependency("fakemodule.submodule", errors="warn")
    assert result is None

    module.__version__ = "1.0.0"  # exact match is OK
    result = import_optional_dependency("fakemodule.submodule")
    assert result is submodule


def test_no_version_raises(monkeypatch):
    name = "fakemodule"
    module = types.ModuleType(name)
    sys.modules[name] = module
    monkeypatch.setitem(_MINIMUM_VERSIONS, name, "1.0.0")

    with pytest.raises(ImportError, match="Can't determine .* fakemodule"):
        import_optional_dependency(name)
