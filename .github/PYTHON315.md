# Python 3.15 CI

Python 3.15 jobs run experimentally on Linux, macOS, and Windows. They use
`continue-on-error` while compatibility is checked and do not declare official
support. Windows follows the existing Python 3.14 path without notebook tests;
Coiled-specific coverage is also excluded by its dependency marker.

On 2026-10-11, the original locked dependencies prevented test collection:
`rpds-py` 0.25.1 failed to build with Python 3.15 on Linux and macOS, and
`cachebox` 5.2.3 failed on Windows because their PyO3 versions rejected 3.15.

On 2026-11-21, the lockfile was updated to `aiohttp` 3.14.5, `greenlet` 3.5.6,
`deepdiff` 9.2.1, `cachebox` 6.2.11, and `rpds-py` 2026.9.1. A local Windows
Python 3.15.0 run on an earlier main checkout passed 1,094 tests, with 42 skipped,
one expected failure, and five unexpected passes, without notebook tests. The CI
matrix on this branch checks the updated main and dependency combination on all
three platforms.

Review the individual 3.15 jobs: their failures do not fail the overall workflow.
Promote Python 3.15 to supported status only after the applicable suites pass
across the matrix and remaining coverage exclusions have been assessed.
