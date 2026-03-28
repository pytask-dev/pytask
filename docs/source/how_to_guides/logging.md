# Manage logging

pytask can capture log records emitted during task execution, show them for failing
tasks, stream them live to the terminal, and write them to a file.

If you do not use Python's [`logging`](https://docs.python.org/3/library/logging.html)
module often, think of log records simply as structured status messages such as
"starting download", "loaded 200 rows", or "publishing failed".

This guide focuses on the most common ways to work with logging in pytask.

## Quick start

If you want to... use this:

- see log messages only when a task fails: run `pytask`
- show only logs in failure reports: run `pytask --show-capture=log`
- see logs immediately while tasks run: run `pytask --log-cli --log-cli-level=INFO`
- save logs to a file: run `pytask --log-file=build.log`
- capture more detailed messages such as `INFO` or `DEBUG`: add `--log-level=INFO` or
    `--log-level=DEBUG`

## A minimal example

```py title="task_logging.py"
import logging
import sys


logger = logging.getLogger(__name__)


def task_prepare_report():
    logger.info("preparing report.txt")


def task_publish_report():
    logger.warning("publishing report is about to fail")
    print("stdout from publish")
    sys.stderr.write("stderr from publish\n")
    raise RuntimeError("simulated publish failure")
```

The most common logging levels are:

- `DEBUG`: very detailed information for debugging
- `INFO`: normal progress messages
- `WARNING`: something unexpected happened, but execution can continue
- `ERROR`: a more serious problem

If you are just getting started, `INFO` and `WARNING` are usually the most useful
levels.

Here is what this looks like with live logging enabled and failure output restricted to
captured logs:

```console
$ pytask --log-cli --log-cli-level=INFO --show-capture=log
```

--8<-- "docs/source/_static/md/logging-live.md"

## Show captured logs for failing tasks

Log records emitted with Python's
[`logging`](https://docs.python.org/3/library/logging.html) module are attached to the
report of a failing task in the same way as captured `stdout` and `stderr`.

```py title="task_logging.py"
import logging


logger = logging.getLogger(__name__)


def task_example():
    logger.warning("something went wrong")
    raise RuntimeError("fail")
```

```console
$ pytask
```

By default, pytask shows captured log output for failing tasks together with the
traceback and any captured `stdout` or `stderr`.

This is useful when a task fails and you want to see what happened right before the
error.

Use `--show-capture` to control which captured output is shown:

```console
$ pytask --show-capture=log
$ pytask --show-capture=all
$ pytask --show-capture=no
```

`--show-capture=log` is useful when you only want log records in the failure report and
want to hide captured `stdout` and `stderr`.

## Control which log records are captured

By default, pytask does not change the logging level. Captured output therefore depends
on your normal logging configuration.

In practice this often means that `WARNING` and `ERROR` messages appear, while `INFO`
and `DEBUG` messages do not, unless you configure logging more explicitly.

Use `--log-level` to set the threshold for captured log records explicitly:

```console
$ pytask --log-level=INFO
$ pytask --log-level=DEBUG
```

As a rule of thumb:

- use `INFO` if you want to see normal progress messages,
- use `DEBUG` only when you need very detailed diagnostics.

This option affects:

- log records attached to failing task reports,
- live logs shown with `--log-cli`,
- exported logs written with `--log-file`.

You can customize the formatting of captured log records with:

```console
$ pytask --log-format="%(asctime)s %(levelname)s %(message)s" \
         --log-date-format="%Y-%m-%d %H:%M:%S"
```

## Stream logs live while tasks run

Use `--log-cli` to print log records directly to the terminal during task execution.

```console
$ pytask --log-cli --log-cli-level=INFO
```

This is helpful when tasks take a while and you want immediate feedback instead of
waiting for the final report.

You can customize live logs separately from the captured report output:

```console
$ pytask --log-cli \
         --log-cli-level=INFO \
         --log-cli-format="%(levelname)s:%(message)s" \
         --log-cli-date-format="%H:%M:%S"
```

If `--log-cli-format` or `--log-cli-date-format` are not provided, pytask falls back to
`--log-format` and `--log-date-format`.

## Write logs to a file

Use `--log-file` to export log records from executed tasks to a file.

```console
$ pytask --log-file=build.log
```

This is useful for CI runs, long builds, or when you want to inspect logs after the run
has finished.

The file is overwritten by default. Use `--log-file-mode=a` to append instead.

```console
$ pytask --log-file=build.log --log-file-mode=a
```

You can control the file output independently:

```console
$ pytask --log-file=build.log \
         --log-file-level=INFO \
         --log-file-format="%(asctime)s %(name)s %(levelname)s %(message)s" \
         --log-file-date-format="%Y-%m-%d %H:%M:%S"
```

Relative log file paths are resolved relative to the project root detected by pytask.

## A good beginner setup

If you want a practical setup without spending much time on logging configuration, this
is a good default:

```console
$ pytask --log-cli --log-cli-level=INFO --log-file=build.log --show-capture=log
```

This gives you:

- live progress messages in the terminal,
- a log file you can inspect later,
- only log output in failure reports, without extra `stdout` and `stderr` noise.

## Configure logging defaults in `pyproject.toml`

All logging options can be configured in `pyproject.toml`.

```toml title="pyproject.toml"
[tool.pytask.ini_options]
log_level = "INFO"
log_format = "%(asctime)s %(levelname)s %(message)s"
log_date_format = "%Y-%m-%d %H:%M:%S"

log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(levelname)s:%(message)s"

log_file = "build.log"
log_file_mode = "w"
log_file_level = "INFO"
log_file_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
log_file_date_format = "%Y-%m-%d %H:%M:%S"
```

## Use logging with the programmatic interface

The same options are available via
[`pytask.build`](../api/functional_interfaces.md#build-workflow).

```py title="build.py"
from pytask import build


session = build(
    log_level="INFO",
    log_cli=True,
    log_cli_level="INFO",
    log_file="build.log",
    log_file_format="%(levelname)s:%(message)s",
)
```
