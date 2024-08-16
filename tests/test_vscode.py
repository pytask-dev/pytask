from __future__ import annotations

import json
import os
import textwrap
from unittest.mock import MagicMock

import pytest
from _pytask.vscode import send_logging_info
from _pytask.vscode import validate_and_return_port
from pytask import ExitCode
from pytask import cli


@pytest.mark.unit()
def test_validate_and_return_port_valid_port():
    assert validate_and_return_port("6000") == 6000


@pytest.mark.unit()
def test_validate_and_return_port_invalid_port():
    with pytest.raises(
        ValueError,
        match="The value provided in the environment variable "
        "PYTASK_VSCODE must be an integer, got not_an_integer instead.",
    ):
        validate_and_return_port("not_an_integer")


@pytest.mark.unit()
def test_send_logging_info(monkeypatch):
    mock_urlopen = MagicMock()
    monkeypatch.setattr("_pytask.vscode.urlopen", mock_urlopen)

    url = "http://localhost:6000/pytask/run"
    data = {"test": "test"}
    timeout = 0.00001
    response = json.dumps(data).encode()

    send_logging_info(url, data, timeout)
    mock_urlopen.assert_called_with(url=url, data=response, timeout=timeout)


@pytest.mark.end_to_end()
def test_vscode_collect_failed(runner, tmp_path, monkeypatch):
    mock_urlopen = MagicMock()
    monkeypatch.setattr("_pytask.vscode.urlopen", mock_urlopen)
    source = """
    raise Exception
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    mock_urlopen.assert_called_with(
        url="http://localhost:6000/pytask/collect",
        data=b'{"exitcode": "COLLECTION_FAILED", "tasks": []}',
        timeout=0.00001,
    )


@pytest.mark.end_to_end()
def test_vscode_collect(runner, tmp_path):
    source = """
    def task_example():
        return
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_vscode_build(runner, tmp_path, monkeypatch):
    mock_urlopen = MagicMock()
    monkeypatch.setattr("_pytask.vscode.urlopen", mock_urlopen)
    source = """
    def task_example():
        return
    def task_raises():
        raise Exception
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert mock_urlopen.call_count == 2
