from __future__ import annotations

from pytask import cli


def test_choices_are_displayed_in_help_page(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[no|stdout|stderr|all]" in result.output
    assert "[sqlite|postgres|mysql|" in result.output
    assert "[fd|no|sys|tee-sys]" in result.output


def test_defaults_are_displayed(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[default: True]" in result.output
