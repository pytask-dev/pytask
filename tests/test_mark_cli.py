import pytest
from pytask.mark.cli import pytask_main


@pytest.mark.end_to_end
def test_show_markers(capsys):
    session = pytask_main({"markers": True})

    assert session.exit_code == 0

    captured = capsys.readouterr()
    assert all(
        marker in captured.out
        for marker in [
            "depends_on",
            "produces",
            "skip",
            "skip_ancestor_failed",
            "skip_unchanged",
        ]
    )
