import textwrap

import pytest
from pytask.mark_ import pytask_main


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


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_markers_option(capsys, tmp_path, config_name):
    tmp_path.joinpath(config_name).write_text(
        textwrap.dedent(
            """
            [pytask]
            markers =
                a1: this is a webtest marker
                a1some: another marker
                nodescription
            """
        )
    )
    session = pytask_main({"paths": tmp_path, "markers": True})

    assert session.exit_code == 0

    captured = capsys.readouterr()
    assert all(marker in captured.out for marker in ["a1", "a1some", "nodescription"])


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
@pytest.mark.parametrize("marker_name", ["lkasd alksds", "1kasd"])
def test_marker_names(tmp_path, marker_name, config_name):
    tmp_path.joinpath(config_name).write_text(
        textwrap.dedent(
            f"""
            [pytask]
            markers =
                {marker_name}
            """
        )
    )
    with pytest.raises(Exception, match="Error while configuring pytask."):
        pytask_main({"paths": tmp_path, "markers": True})
