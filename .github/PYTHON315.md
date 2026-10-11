# Python 3.15 CI blockers

Python 3.15 runs on Linux, macOS, and Windows in the test matrix. These jobs are
experimental and use `continue-on-error` while the blockers below are investigated.
Python 3.11 through 3.14 retain their existing failure behavior. Adding the matrix
row does not yet declare Python 3.15 support in the package classifiers.

## Dependency installation

Checked on 2026-10-11 with CPython 3.15.0 on Windows and the repository's unchanged
`uv.lock`:

| Dependency | Locked version | Observation | Next step |
| --- | --- | --- | --- |
| `aiohttp` | 3.14.3 | No CPython 3.15 wheels in the lock; installation attempts a source build. | Evaluate 3.14.5, which publishes CPython 3.15 wheels. |
| `greenlet` | 3.2.3 | No CPython 3.15 wheels in the lock; installation attempts a source build. | Evaluate a newer version with CPython 3.15 wheels, such as 3.5.6. |
| `cachebox` | 5.2.3 | No CPython 3.15 wheels in the lock. `deepdiff` 9.1.0 requires `cachebox>=5.2,<6`, preventing an upgrade to 6.2.8, which has CPython 3.15 wheels. | Find a compatible `cachebox` 5.x release or update the `deepdiff` constraint upstream. |
| `pywin32` | 310 | No CPython 3.14 or 3.15 wheels in the lock. The existing `nbmake` dependency marker excludes Windows on these versions. | Evaluate `pywin32` 312 and restore Windows notebook coverage after validating its dependency chain. |

Sources: [aiohttp 3.14.5](https://pypi.org/project/aiohttp/3.14.5/#files),
[greenlet 3.5.6](https://pypi.org/project/greenlet/3.5.6/#files),
[cachebox 6.2.8](https://pypi.org/project/cachebox/6.2.8/#files),
[deepdiff 9.1.0 metadata](https://pypi.org/pypi/deepdiff/9.1.0/json), and
[pywin32 312](https://pypi.org/project/pywin32/312/#files).

Reproduce the locked-environment check with a current `uv`:

```console
uv sync --python 3.15 --group test
uv sync --python 3.15 --group test --no-build
```

The first command failed locally before tests ran: the `aiohttp` source build
could not find the Windows SDK header `io.h`. The second command confirms that the
locked `aiohttp` distribution has no compatible Windows wheel. A diagnostic update
of `aiohttp`, `greenlet`, and `cachebox` still selected `cachebox` 5.2.3 because of
the `deepdiff` constraint; that source build failed because `link.exe` was unavailable.
These compiler failures describe the local environment, not proven upstream
incompatibilities. CI runner results must establish whether source builds work there.
The diagnostic lock changes are not included in this PR.

## Runtime availability and test coverage

[Python 3.15.0 was released on 2026-10-09](https://www.python.org/downloads/release/python-3150/).
Local `uv` 0.12.17 offered only 3.15.0rc2, while `uvx uv@latest` installed 3.15.0.
Use a current `uv` when reproducing the jobs; the workflow uses `setup-uv` without
pinning an old `uv` version.

Windows 3.15 follows the existing Windows 3.14 path without `--nbmake`, matching
the dependency marker. Linux and macOS attempt the normal notebook-inclusive suite.
The highest-resolution job stays on Python 3.14 until the experimental jobs can run
successfully. The existing Coiled dependency marker also excludes Python 3.15, so
the Coiled-specific test remains skipped.

No claim about pytask runtime compatibility can be made from the local run because
dependency installation failed before test collection. Record CI failures here as
they become available. Remove `continue-on-error` and add the Python 3.15 classifier
only after dependency installation and the applicable test suites pass on all three
operating systems.
