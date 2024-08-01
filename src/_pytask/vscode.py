"""Contains Code for VSCode Logging."""

from __future__ import annotations

import contextlib
import json
import os
from threading import Thread
from typing import TYPE_CHECKING
from typing import Any
from urllib import request

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


def send_logging_info(url: str, data: dict[str, Any], timeout: float) -> None:
    """Send logging information to the provided port."""
    with contextlib.suppress(Exception):
        response = json.dumps(data).encode("utf-8")
        req = request.Request(url, data=response)  # noqa: S310
        req.add_header("Content-Type", "application/json; charset=utf-8")
        request.urlopen(req, timeout=timeout)  # noqa: S310


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
            port = 6000
        exitcode = "OK"
        for report in reports:
            if report.outcome == CollectionOutcome.FAIL:
                exitcode = "COLLECTION_FAILED"
        result = [
            {"name": task.name, "path": str(task.path)}
            if isinstance(task, PTaskWithPath)
            else {"name": task.name, "path": ""}
            for task in tasks
        ]
        url = f"http://localhost:{port}/pytask/collect"
        thread = Thread(
            target=send_logging_info,
            args=(
                url,
                {"exitcode": exitcode, "tasks": result},
                0.00001,
            ),
        )
        thread.start()


@hookimpl(tryfirst=True)
def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:  # noqa: ARG001
    """Start threads to send logging information for executed tasks."""
    if os.environ.get("PYTASK_VSCODE") is not None:
        try:
            port = int(os.environ["PYTASK_VSCODE"])
        except ValueError:
            port = 6000
        if report.outcome == TaskOutcome.FAIL and report.exc_info is not None:
            result = {
                "name": report.task.name,
                "outcome": str(report.outcome),
                "exc_info": render_to_string(Traceback(report.exc_info), console),
            }
        else:
            result = {
                "name": report.task.name,
                "outcome": str(report.outcome),
            }
        url = f"http://localhost:{port}/pytask/run"
        thread = Thread(
            target=send_logging_info,
            args=(url, result, 0.00001),
        )
        thread.start()
