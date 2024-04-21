from __future__ import annotations

import pytest
from pytask import cli


@pytest.mark.end_to_end()
def test_choices_are_displayed_in_help_page(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[no|stdout|stderr|all]" in result.output
    assert "[fd|no|sys|tee-sys]" in result.output


@pytest.mark.end_to_end()
def test_defaults_are_displayed(runner):
    result = runner.invoke(cli, ["build", "--help"])
    assert "[default: all]" in result.output
