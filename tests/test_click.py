from __future__ import annotations

import enum

import click
import pytest
from pytask import cli
from pytask import EnumChoice


@pytest.mark.end_to_end()
def test_choices_are_displayed_in_help_page(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[no|stdout|stderr|all]" in result.output
    assert "[fd|no|sys|tee-sys]" in result.output


@pytest.mark.end_to_end()
def test_defaults_are_displayed(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[default: all]" in result.output


@pytest.mark.unit()
@pytest.mark.parametrize("method", ["first", "second"])
def test_enum_choice(runner, method):
    class Method(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @click.command()
    @click.option("--method", type=EnumChoice(Method))
    def test(method):
        print(f"method={method}")  # noqa: T201

    result = runner.invoke(test, ["--method", method])

    assert result.exit_code == 0
    assert f"method=Method.{method.upper()}" in result.output


@pytest.mark.unit()
def test_enum_choice_error(runner):
    class Method(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @click.command()
    @click.option("--method", type=EnumChoice(Method))
    def test():
        ...

    result = runner.invoke(test, ["--method", "third"])

    assert result.exit_code == 2
    assert "Invalid value for '--method': " in result.output
    assert "'third' is not one of 'first', 'second'." in result.output
