"""Contains Code for VSCode Logging."""

from __future__ import annotations

import contextlib
import json
import os
from threading import Thread
from typing import TYPE_CHECKING
from typing import Any
from urllib.request import Request
from urllib.request import urlopen

from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import render_to_string
from _pytask.nodes import PTaskWithPath
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.reports import CollectionReport
    from _pytask.reports import ExecutionReport
    from _pytask.session import Session


TIMEOUT = 0.00001
DEFAULT_VSCODE_PORT = 6000


def send_logging_info(url: str, data: dict[str, Any], timeout: float) -> None:
    """Send logging information to the provided port."""
    # TODO: Can you add a unit test for this function? And mark it with
    # pytest.mark.unit()

    with contextlib.suppress(Exception):
        # TODO: Why do you suppress all exceptions? Maybe we should fix S310

        response = json.dumps(data).encode("utf-8")
        req = Request(url, data=response)  # noqa: S310
        req.add_header("Content-Type", "application/json; charset=utf-8")
        urlopen(req, timeout=timeout)  # noqa: S310


@hookimpl(tryfirst=True)
def pytask_collect_log(
    session: Session, reports: list[CollectionReport], tasks: list[PTask]
) -> None:
    """Start threads to send logging information for collected tasks."""
    if (
        os.environ.get("PYTASK_VSCODE") is not None
        and session.config["command"] == "collect"
    ):
        try:
            port = int(os.environ["PYTASK_VSCODE"])
        except ValueError:
            # TODO: When does this case happen?
            port = DEFAULT_VSCODE_PORT

        exitcode = "OK"
        for report in reports:
            if report.outcome == CollectionOutcome.FAIL:
                exitcode = "COLLECTION_FAILED"

        result = []
        for task in tasks:
            path = str(task.path) if isinstance(task, PTaskWithPath) else ""
            result.append({"name": task.name, "path": path})

        thread = Thread(
            target=send_logging_info,
            kwargs={
                "url": f"http://localhost:{port}/pytask/collect",
                "data": {"exitcode": exitcode, "tasks": result},
                "timeout": TIMEOUT,
            },
        )
        thread.start()


@hookimpl(tryfirst=True)
def pytask_execute_task_log_end(
    session: Session,  # noqa: ARG001
    report: ExecutionReport,
) -> None:
    """Start threads to send logging information for executed tasks."""
    if os.environ.get("PYTASK_VSCODE") is not None:
        try:
            port = int(os.environ["PYTASK_VSCODE"])
        except ValueError:
            # TODO: When does this case happen?
            port = DEFAULT_VSCODE_PORT

        result = {
            "name": report.task.name,
            "outcome": str(report.outcome),
        }
        if report.outcome == TaskOutcome.FAIL and report.exc_info is not None:
            result["exc_info"] = render_to_string(Traceback(report.exc_info), console)

        thread = Thread(
            target=send_logging_info,
            kwargs={
                "url": f"http://localhost:{port}/pytask/run",
                "data": result,
                "timeout": TIMEOUT,
            },
        )
        thread.start()
