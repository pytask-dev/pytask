from __future__ import annotations

import pytest
from pytask import CollectionReport
from pytask import DagReport
from pytask import ExecutionReport
from pytask import PReport


@pytest.mark.parametrize("report", [CollectionReport, DagReport, ExecutionReport])
def test_reports_follow_protocol(report):
    assert isinstance(report, PReport)
