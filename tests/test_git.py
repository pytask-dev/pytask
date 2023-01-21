from __future__ import annotations

import pytest
from _pytask.git import is_git_installed


@pytest.mark.unit()
@pytest.mark.parametrize(("mock_return", "expected"), [(True, True), (None, False)])
def test_is_git_installed(monkeypatch, mock_return, expected):
    monkeypatch.setattr(
        "_pytask.git.shutil.which", lambda *x: mock_return,  # noqa: ARG005
    )
    result = is_git_installed()
    assert result is expected
