from __future__ import annotations

import pytest
from _pytask.reports import CollectionReport
from _pytask.reports import ExecutionReport
from pytask import CollectionOutcome
from pytask import count_outcomes
from pytask import TaskOutcome


@pytest.mark.unit()
@pytest.mark.parametrize("outcome_in_report", CollectionOutcome)
def test_count_outcomes_collection(outcome_in_report):
    reports = [CollectionReport(outcome_in_report, None, None)]

    counts = count_outcomes(reports, CollectionOutcome)

    for outcome, count in counts.items():
        if outcome == outcome_in_report:
            assert count == 1
        else:
            assert count == 0


@pytest.mark.unit()
@pytest.mark.parametrize("outcome_in_report", TaskOutcome)
def test_count_outcomes_tasks(outcome_in_report):
    reports = [ExecutionReport(None, outcome_in_report, None, None)]

    counts = count_outcomes(reports, TaskOutcome)

    for outcome, count in counts.items():
        if outcome == outcome_in_report:
            assert count == 1
        else:
            assert count == 0
