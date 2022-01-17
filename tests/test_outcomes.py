from __future__ import annotations

import pytest
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import count_outcomes
from _pytask.outcomes import TaskOutcome
from _pytask.report import CollectionReport
from _pytask.report import ExecutionReport


@pytest.mark.parametrize("outcome_in_report", CollectionOutcome)
def test_count_outcomes_collection(outcome_in_report):
    reports = [CollectionReport(outcome_in_report, None, None)]

    counts = count_outcomes(reports, CollectionOutcome)

    for outcome, count in counts.items():
        if outcome == outcome_in_report:
            assert count == 1
        else:
            assert count == 0


@pytest.mark.parametrize("outcome_in_report", TaskOutcome)
def test_count_outcomes_tasks(outcome_in_report):
    reports = [ExecutionReport(None, outcome_in_report, None, None)]

    counts = count_outcomes(reports, TaskOutcome)

    for outcome, count in counts.items():
        if outcome == outcome_in_report:
            assert count == 1
        else:
            assert count == 0
