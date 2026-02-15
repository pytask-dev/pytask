# Changes

The document records all past pytask releases and what went into them in reverse
chronological order. Releases follow [semantic versioning](https://semver.org/) and all
releases are available on [PyPI](https://pypi.org/project/pytask) and
[Anaconda.org](https://anaconda.org/conda-forge/pytask).

## Unreleased

- [#744](https://github.com/pytask-dev/pytask/pull/744) Removed the direct dependency on attrs and migrated internal models to
  dataclasses.
- [#766](https://github.com/pytask-dev/pytask/pull/766) moves runtime profiling persistence from SQLite to a JSON snapshot plus
  append-only journal in `.pytask/`, keeping runtime data resilient to crashes and
  compacted on normal build exits.
- [#776](https://github.com/pytask-dev/pytask/pull/776) clears decoration-time `annotation_locals` snapshots after collection so
  task functions remain picklable in process-based parallel backends.

## 0.5.8 - 2025-12-30

- [#710](https://github.com/pytask-dev/pytask/pull/710) adds support for Python 3.14.
- [#724](https://github.com/pytask-dev/pytask/pull/724) handles lazy annotations for task generators in Python 3.14.
- [#725](https://github.com/pytask-dev/pytask/pull/725) fixes the pickle node hash test by accounting for Python 3.14's
  default pickle protocol.
- [#726](https://github.com/pytask-dev/pytask/pull/726) adapts the interactive debugger integration to Python 3.14's
  updated `pdb` behaviour and keeps pytest-style capturing intact.
- [#732](https://github.com/pytask-dev/pytask/pull/732) fixes importing packages with missing `__init__.py` files.
- [#739](https://github.com/pytask-dev/pytask/pull/739) closes file descriptors for the capture manager between CLI runs and
  disposes stale database engines to prevent hitting OS file descriptor limits in
  large test runs.
- [#734](https://github.com/pytask-dev/pytask/pull/734) migrates from mypy to ty for type checking.
- [#736](https://github.com/pytask-dev/pytask/pull/736) updates the comparison to other tools documentation and adds a section on
  the Common Workflow Language (CWL) and WorkflowHub.
- [#730](https://github.com/pytask-dev/pytask/pull/730) updates GitHub Actions dependencies.
- [#731](https://github.com/pytask-dev/pytask/pull/731) enables automerge for pre-commit and Dependabot.
- [#733](https://github.com/pytask-dev/pytask/pull/733) and [#727](https://github.com/pytask-dev/pytask/pull/727) refresh pre-commit hooks.
- [#737](https://github.com/pytask-dev/pytask/pull/737) enables merge groups.

## 0.5.7 - 2025-11-22

- [#721](https://github.com/pytask-dev/pytask/pull/721) clarifies the documentation on repeated tasks in notebooks.
- [#723](https://github.com/pytask-dev/pytask/pull/723) fixes an issue with defaults for click options. Thanks to [@DrorSh](https://github.com/DrorSh) for contributing the fix!

## 0.5.6 - 2025-10-31

- [#703](https://github.com/pytask-dev/pytask/pull/703) fixes [#701](https://github.com/pytask-dev/pytask/issues/701) by allowing `--capture tee-sys` again.
- [#704](https://github.com/pytask-dev/pytask/pull/704) adds the `--explain` flag to show why tasks would be executed. Closes [#466](https://github.com/pytask-dev/pytask/issues/466).
- [#706](https://github.com/pytask-dev/pytask/pull/706) disables syntax highlighting for platform version information in session header.
- [#707](https://github.com/pytask-dev/pytask/pull/707) drops support for Python 3.9 as it has reached end of life.
- [#708](https://github.com/pytask-dev/pytask/pull/708) updates mypy and fixes type issues.
- [#709](https://github.com/pytask-dev/pytask/pull/709) adds uv pre-commit check.
- [#710](https://github.com/pytask-dev/pytask/pull/710) adds support for Python 3.14.
- [#713](https://github.com/pytask-dev/pytask/pull/713) removes uv as a test dependency. Closes [#712](https://github.com/pytask-dev/pytask/issues/712). Thanks to [@erooke](https://github.com/erooke)!
- [#718](https://github.com/pytask-dev/pytask/pull/718) fixes [#717](https://github.com/pytask-dev/pytask/issues/717) by properly parsing the `pdbcls` configuration option from config files. Thanks to [@MImmesberger](https://github.com/MImmesberger) for the report!
- [#719](https://github.com/pytask-dev/pytask/pull/719) fixes repeated tasks with the same function name in the programmatic interface to ensure all tasks execute correctly.

## 0.5.5 - 2025-07-25

- [#692](https://github.com/pytask-dev/pytask/pull/692) documents how to use pytask with workspaces.
- [#694](https://github.com/pytask-dev/pytask/pull/694) fixes [#693](https://github.com/pytask-dev/pytask/issues/693) so that missing dependencies are detected in some cases. Thanks to [@timmens](https://github.com/timmens) for the report!

## 0.5.4 - 2025-06-08

- [#676](https://github.com/pytask-dev/pytask/pull/676) ensures compatibility with click >8.2.0.
- [#680](https://github.com/pytask-dev/pytask/pull/680) uses uv everywhere.
- [#684](https://github.com/pytask-dev/pytask/pull/684) adds tests for lowest and highest dependency resolutions.
- [#685](https://github.com/pytask-dev/pytask/pull/685) fixes the file urls in task and node names and enables colors and icons in
  Windows terminals.
- [#686](https://github.com/pytask-dev/pytask/pull/686) updates the changelog and adds it to the repository root.

## 0.5.3 - 2025-05-16

- [#650](https://github.com/pytask-dev/pytask/pull/650) allows to identify from which data catalog a node is coming from. Thanks
  to [@felixschmitz](https://github.com/felixschmitz) for the report! The feature is enabled by adding an
  `attributes` field on `PNode` and `PProvisionalNode` that will be mandatory on custom
  nodes in v0.6.0.
- [#662](https://github.com/pytask-dev/pytask/pull/662) adds the `.pixi` folder to be ignored by default during the collection.
- [#671](https://github.com/pytask-dev/pytask/pull/671) enhances the documentation on complex repetitions. Closes [#670](https://github.com/pytask-dev/pytask/issues/670).
- [#673](https://github.com/pytask-dev/pytask/pull/673) adds de-/serializer function attributes to the `PickleNode`. Closes
  [#669](https://github.com/pytask-dev/pytask/issues/669).
- [#677](https://github.com/pytask-dev/pytask/pull/677) excludes the latest click v8.2.0 due to compatibility issues.
- [#678](https://github.com/pytask-dev/pytask/pull/678) enables some tests in CI or offline, removes refurb.

## 0.5.2 - 2024-12-19

- [#633](https://github.com/pytask-dev/pytask/pull/633) adds support for Python 3.13 and drops support for 3.8.
- [#640](https://github.com/pytask-dev/pytask/pull/640) stops the live display when an exception happened during the execution.
- [#646](https://github.com/pytask-dev/pytask/pull/646) adds a `.gitignore` to the `.pytask/` folder to exclude it from version
  control.
- [#656](https://github.com/pytask-dev/pytask/pull/656) fixes the return type of the hash function for `PythonNode`s.
  Thanks to [@axtimhaus](https://github.com/axtimhaus) for reporting the issue.
- [#657](https://github.com/pytask-dev/pytask/pull/657) documents `pipefunc`, another tool for executing graphs consisting out of
  functions.

## 0.5.1 - 2024-07-20

- [#616](https://github.com/pytask-dev/pytask/pull/616) and [#632](https://github.com/pytask-dev/pytask/pull/632) redesign the guide on "Scaling Tasks".
- [#617](https://github.com/pytask-dev/pytask/pull/617) fixes an interaction with provisional nodes and `@mark.persist`.
- [#618](https://github.com/pytask-dev/pytask/pull/618) ensures that `root_dir` of `DirectoryNode` is created before the task is
  executed.
- [#619](https://github.com/pytask-dev/pytask/pull/619) makes coiled an optional import for tests. Thanks to [@erooke](https://github.com/erooke).
- [#620](https://github.com/pytask-dev/pytask/pull/620) makes tests more flexible about their location. Thanks to [@erooke](https://github.com/erooke).
- [#621](https://github.com/pytask-dev/pytask/pull/621) fixes the pull requests template.
- [#626](https://github.com/pytask-dev/pytask/pull/626) resolves an issue with rerunning tasks via the programmatic API. Closes
  [#625](https://github.com/pytask-dev/pytask/issues/625). Thanks to @noppelmax for the issue!
- [#627](https://github.com/pytask-dev/pytask/pull/627) adds a warning when users explicitly pass files to pytask that pytask is
  going to ignore because they do not match a pattern. Happens quite often when the task
  module's name does not start with `task_`.
- [#628](https://github.com/pytask-dev/pytask/pull/628) fixes duplicated collection of task modules. Fixes [#624](https://github.com/pytask-dev/pytask/issues/624). Thanks to
  [@timmens](https://github.com/timmens) for the issue.
- [#631](https://github.com/pytask-dev/pytask/pull/631) fixes display issues with the programmatic interface by giving each
  `_pytask.live.LiveManager` its own `rich.live.Live`.

## 0.5.0 - 2024-05-26

- [#548](https://github.com/pytask-dev/pytask/pull/548) fixes the type hints for `pytask.Task.execute` and
  `pytask.TaskWithoutPath.execute`. Thanks to [@Ostheer](https://github.com/Ostheer).
- [#551](https://github.com/pytask-dev/pytask/pull/551) removes the deprecated `@pytask.mark.depends_on` and
  `@pytask.mark.produces`.
- [#552](https://github.com/pytask-dev/pytask/pull/552) removes the deprecated `@pytask.mark.task`.
- [#553](https://github.com/pytask-dev/pytask/pull/553) deprecates `paths` as a string in configuration and ensures that paths
  passed via the command line are relative to CWD and paths in the configuration
  relative to the config file.
- [#555](https://github.com/pytask-dev/pytask/pull/555) uses new-style hook wrappers and requires pluggy 1.3 for typing.
- [#557](https://github.com/pytask-dev/pytask/pull/557) fixes an issue with `@task(after=...)` in notebooks and terminals.
- [#566](https://github.com/pytask-dev/pytask/pull/566) makes universal-pathlib an official dependency.
- [#567](https://github.com/pytask-dev/pytask/pull/567) adds uv to the CI workflow for faster installation.
- [#568](https://github.com/pytask-dev/pytask/pull/568) restricts `task_files` to a list of patterns and raises a better error.
- [#569](https://github.com/pytask-dev/pytask/pull/569) removes the hooks related to the creation of the DAG.
- [#571](https://github.com/pytask-dev/pytask/pull/571) removes redundant calls to `PNode.state()` which causes a high penalty for
  remote files.
- [#573](https://github.com/pytask-dev/pytask/pull/573) removes the `pytask_execute_create_scheduler` hook.
- [#579](https://github.com/pytask-dev/pytask/pull/579) fixes an interaction with `--pdb` and `--trace` and task that return. The
  debugging modes swallowed the return and `None` was returned. Closes [#574](https://github.com/pytask-dev/pytask/issues/574).
- [#581](https://github.com/pytask-dev/pytask/pull/581) simplifies the code for tracebacks and unpublishes some utility functions.
- [#586](https://github.com/pytask-dev/pytask/pull/586) improves linting.
- [#587](https://github.com/pytask-dev/pytask/pull/587) improves typing of `capture.py`.
- [#588](https://github.com/pytask-dev/pytask/pull/588) resets class variables of `ExecutionReport` and `Traceback`.
- [#589](https://github.com/pytask-dev/pytask/pull/589) enables `import_path` to resolve the root path and module name of an
  imported file.
- [#590](https://github.com/pytask-dev/pytask/pull/590) fixes an error introduced in [#588](https://github.com/pytask-dev/pytask/pull/588).
- [#591](https://github.com/pytask-dev/pytask/pull/591) invalidates the cache of fsspec when checking whether a remote file
  exists. Otherwise, a remote file might be reported as missing although it was just
  created. See https://github.com/fsspec/s3fs/issues/851 for more info.
- [#593](https://github.com/pytask-dev/pytask/pull/593) recreate `PythonNode`s every run since they carry the `_NoDefault` enum as
  the value whose state is `None`.
- [#594](https://github.com/pytask-dev/pytask/pull/594) publishes `NodeLoadError`.
- [#595](https://github.com/pytask-dev/pytask/pull/595) stops unwrapping task functions until a `coiled.function.Function`.
- [#596](https://github.com/pytask-dev/pytask/pull/596) add project management with rye.
- [#598](https://github.com/pytask-dev/pytask/pull/598) replaces requests with httpx.
- [#599](https://github.com/pytask-dev/pytask/pull/599) adds a test fixture for switching the cwd.
- [#600](https://github.com/pytask-dev/pytask/pull/600) refactors test using subprocesses.
- [#603](https://github.com/pytask-dev/pytask/pull/603) fixes an example in the documentation about capturing warnings.
- [#604](https://github.com/pytask-dev/pytask/pull/604) fixes some examples with `PythonNode`s in the documentation.
- [#605](https://github.com/pytask-dev/pytask/pull/605) improves checks and CI.
- [#606](https://github.com/pytask-dev/pytask/pull/606) improves the documentation for data catalogs.
- [#609](https://github.com/pytask-dev/pytask/pull/609) allows a pending status for tasks. Useful for async backends implemented
  in pytask-parallel.
- [#611](https://github.com/pytask-dev/pytask/pull/611) removes the initial task execution status from
  `pytask_execute_task_log_start`.
- [#612](https://github.com/pytask-dev/pytask/pull/612) adds validation for data catalog names.

## 0.4.7 - 2024-03-19

- [#580](https://github.com/pytask-dev/pytask/pull/580) is a backport of [#579](https://github.com/pytask-dev/pytask/pull/579).

## 0.4.6 - 2024-03-13

- [#576](https://github.com/pytask-dev/pytask/pull/576) fixes accidentally collecting `pytask.MarkGenerator` when using
  `from pytask import mark`.

## 0.4.5 - 2024-01-09

- [#515](https://github.com/pytask-dev/pytask/pull/515) enables tests with graphviz in CI. Thanks to [@NickCrews](https://github.com/NickCrews).
- [#517](https://github.com/pytask-dev/pytask/pull/517) raises an error when the configuration file contains a non-existing path
  (fixes #514). It also warns if the path is configured as a string, not a list of
  strings.
- [#519](https://github.com/pytask-dev/pytask/pull/519) raises an error when builtin functions are wrapped with
  `pytask.task`. Closes [#512](https://github.com/pytask-dev/pytask/issues/512).
- [#521](https://github.com/pytask-dev/pytask/pull/521) raises an error message when imported functions are wrapped with
  `@task` in a task module. Fixes [#513](https://github.com/pytask-dev/pytask/issues/513).
- [#522](https://github.com/pytask-dev/pytask/pull/522) improves the issue templates.
- [#523](https://github.com/pytask-dev/pytask/pull/523) refactors `_pytask.console._get_file`.
- [#524](https://github.com/pytask-dev/pytask/pull/524) improves some linting and formatting rules.
- [#525](https://github.com/pytask-dev/pytask/pull/525) enables pytask to work with remote files using universal_pathlib.
- [#528](https://github.com/pytask-dev/pytask/pull/528) improves the codecov setup and coverage.
- [#535](https://github.com/pytask-dev/pytask/pull/535) reenables and fixes tests with Jupyter.
- [#536](https://github.com/pytask-dev/pytask/pull/536) allows partialed functions to be task functions.
- [#538](https://github.com/pytask-dev/pytask/pull/538) updates the documentation. For example, colon fences are replaced by
  backticks to allow formatting all pages by mdformat.
- [#539](https://github.com/pytask-dev/pytask/pull/539) implements the `hook_module` configuration value and
  `--hook-module` commandline option to register hooks.
- [#540](https://github.com/pytask-dev/pytask/pull/540) changes the CLI entry-point and allow `pytask.build(tasks=task_func)` as
  the signatures suggested.
- [#542](https://github.com/pytask-dev/pytask/pull/542) refactors the plugin manager.
- [#543](https://github.com/pytask-dev/pytask/pull/543) fixes imports in tests and related issues.
- [#544](https://github.com/pytask-dev/pytask/pull/544) requires sqlalchemy `>=2` and upgrades the syntax.
- [#545](https://github.com/pytask-dev/pytask/pull/545) finalizes the release.

## 0.4.4 - 2023-12-04

- [#509](https://github.com/pytask-dev/pytask/pull/509) improves the documentation.
- [#510](https://github.com/pytask-dev/pytask/pull/510) fixes typing issues with the `pytask.DataCatalog`.

## 0.4.3 - 2023-12-01

- [#483](https://github.com/pytask-dev/pytask/pull/483) simplifies the teardown of a task.
- [#484](https://github.com/pytask-dev/pytask/pull/484) raises an informative error message when directories instead of files are
  used with path nodes.
- [#485](https://github.com/pytask-dev/pytask/pull/485) adds missing steps to unconfigure pytask after the job is done, which
  caused flaky tests.
- [#486](https://github.com/pytask-dev/pytask/pull/486) adds default names to `pytask.PPathNode`.
- [#487](https://github.com/pytask-dev/pytask/pull/487) implements task generators and provisional nodes.
- [#488](https://github.com/pytask-dev/pytask/pull/488) raises an error when an invalid value is used in a return annotation.
- [#489](https://github.com/pytask-dev/pytask/pull/489) and [#491](https://github.com/pytask-dev/pytask/pull/491) simplifies parsing products and does not raise an error
  when a product annotation is used with the argument name `produces`. And allow
  `produces` to intake any node.
- [#490](https://github.com/pytask-dev/pytask/pull/490) refactors and better tests parsing of dependencies.
- [#493](https://github.com/pytask-dev/pytask/pull/493) allows tasks to depend on other tasks.
- [#496](https://github.com/pytask-dev/pytask/pull/496) makes pytask even lazier. Now, when a task produces a node whose hash
  remains the same, the consecutive tasks are not executed. It remained from when pytask
  relied on timestamps.
- [#497](https://github.com/pytask-dev/pytask/pull/497) removes unnecessary code in the collection of tasks.
- [#498](https://github.com/pytask-dev/pytask/pull/498) fixes an error when using `pytask.Task` and
  `pytask.TaskWithoutPath` in task modules.
- [#500](https://github.com/pytask-dev/pytask/pull/500) refactors the dependencies for tests.
- [#501](https://github.com/pytask-dev/pytask/pull/501) removes `MetaNode`.
- [#508](https://github.com/pytask-dev/pytask/pull/508) catches objects that pretend to be a `pytask.PTask`. Fixes
  [#507](https://github.com/pytask-dev/pytask/issues/507).

## 0.4.2 - 2023-11-08

- [#449](https://github.com/pytask-dev/pytask/pull/449) simplifies the code building of the plugin manager.
- [#451](https://github.com/pytask-dev/pytask/pull/451) improves `collect_command.py` and renames `graph.py` to `dag_command.py`.
- [#454](https://github.com/pytask-dev/pytask/pull/454) removes more `.svg`s and replaces them with animations.
- [#455](https://github.com/pytask-dev/pytask/pull/455) adds more explanation when `pytask.PNode.load` fails during the
  execution.
- [#456](https://github.com/pytask-dev/pytask/pull/456) refers to the source code on Github when clicking on a source link.
- [#457](https://github.com/pytask-dev/pytask/pull/457) refactors everything around formatting node names.
- [#459](https://github.com/pytask-dev/pytask/pull/459) adds a pre-commit hook to sort `__all__`.
- [#460](https://github.com/pytask-dev/pytask/pull/460) simplifies removing internal tracebacks from exceptions with a cause.
- [#463](https://github.com/pytask-dev/pytask/pull/463) raises an error when a task function is not defined inside the loop body.
- [#464](https://github.com/pytask-dev/pytask/pull/464) improves pinned dependencies.
- [#465](https://github.com/pytask-dev/pytask/pull/465) adds test to ensure internal tracebacks are removed by reports.
- [#466](https://github.com/pytask-dev/pytask/pull/466) implements hashing for files instead of modification timestamps.
- [#470](https://github.com/pytask-dev/pytask/pull/470) moves `.pytask.sqlite3` to `.pytask`.
- [#472](https://github.com/pytask-dev/pytask/pull/472) adds `is_product` to `pytask.PNode.load`.
- [#473](https://github.com/pytask-dev/pytask/pull/473) adds signatures to nodes which decouples an identifier from a name.
- [#477](https://github.com/pytask-dev/pytask/pull/477) updates the PyPI action.
- [#478](https://github.com/pytask-dev/pytask/pull/478) replaces black with ruff-format.
- [#479](https://github.com/pytask-dev/pytask/pull/479) gives skips a higher precedence as an outcome than ancestor failed.
- [#480](https://github.com/pytask-dev/pytask/pull/480) removes the check for missing root nodes from the generation of the DAG.
  It is delegated to the check during the execution.
- [#481](https://github.com/pytask-dev/pytask/pull/481) improves coverage.
- [#482](https://github.com/pytask-dev/pytask/pull/482) correctly handles names and signatures of `pytask.PythonNode`.

## 0.4.1 - 2023-10-11

- [#443](https://github.com/pytask-dev/pytask/pull/443) ensures that `PythonNode.name` is always unique by only handling it
  internally.
- [#444](https://github.com/pytask-dev/pytask/pull/444) moves all content of `setup.cfg` to `pyproject.toml`.
- [#446](https://github.com/pytask-dev/pytask/pull/446) refactors `create_name_of_python_node` and fixes `PythonNode`s as returns.
- [#447](https://github.com/pytask-dev/pytask/pull/447) simplifies the `tree_map` code while generating the DAG.
- [#448](https://github.com/pytask-dev/pytask/pull/448) fixes handling multiple product annotations of a task.

## 0.4.0 - 2023-10-07

- [#323](https://github.com/pytask-dev/pytask/pull/323) remove Python 3.7 support and use a new Github action to provide mamba.
- [#384](https://github.com/pytask-dev/pytask/pull/384) allows to parse dependencies from every function argument if `depends_on`
  is not present.
- [#387](https://github.com/pytask-dev/pytask/pull/387) replaces pony with sqlalchemy.
- [#391](https://github.com/pytask-dev/pytask/pull/391) removes `@pytask.mark.parametrize`.
- [#394](https://github.com/pytask-dev/pytask/pull/394) allows to add products with `typing.Annotated` and
  `pytask.Product`.
- [#395](https://github.com/pytask-dev/pytask/pull/395) refactors all occurrences of pybaum to `_pytask.tree_util`.
- [#396](https://github.com/pytask-dev/pytask/pull/396) replaces pybaum with optree and adds paths to the name of
  `pytask.PythonNode`'s allowing for better hashing.
- [#397](https://github.com/pytask-dev/pytask/pull/397) adds support for `typing.NamedTuple` and attrs classes in
  `@pytask.mark.task(kwargs=...)`.
- [#398](https://github.com/pytask-dev/pytask/pull/398) deprecates the decorators `@pytask.mark.depends_on` and
  `@pytask.mark.produces`.
- [#402](https://github.com/pytask-dev/pytask/pull/402) replaces ABCs with protocols allowing for more flexibility for users
  implementing their own nodes.
- [#404](https://github.com/pytask-dev/pytask/pull/404) allows to use function returns to define task products.
- [#406](https://github.com/pytask-dev/pytask/pull/406) allows to match function returns to node annotations with prefix trees.
- [#408](https://github.com/pytask-dev/pytask/pull/408) removes `.value` from `Node` protocol.
- [#409](https://github.com/pytask-dev/pytask/pull/409) make `.from_annot` an optional feature of nodes.
- [#410](https://github.com/pytask-dev/pytask/pull/410) allows to pass functions to `PythonNode(hash=...)`.
- [#411](https://github.com/pytask-dev/pytask/pull/411) implements a new functional interface and adds experimental support for
  defining and running tasks in REPLs or Jupyter notebooks.
- [#412](https://github.com/pytask-dev/pytask/pull/412) adds protocols for tasks.
- [#413](https://github.com/pytask-dev/pytask/pull/413) removes scripts to generate `.svg`s.
- [#414](https://github.com/pytask-dev/pytask/pull/414) allow more ruff rules.
- [#416](https://github.com/pytask-dev/pytask/pull/416) removes `.from_annot` again.
- [#417](https://github.com/pytask-dev/pytask/pull/417) deprecates `pytask.mark.task` in favor of `pytask.task`.
- [#418](https://github.com/pytask-dev/pytask/pull/418) fixes and error and simplifies code in `dag.py`.
- [#420](https://github.com/pytask-dev/pytask/pull/420) converts `DeprecationWarning`s to `FutureWarning`s for the deprecated
  decorators.
- [#421](https://github.com/pytask-dev/pytask/pull/421) removes the deprecation warning when `produces` is used as an magic
  function keyword to define products.
- [#423](https://github.com/pytask-dev/pytask/pull/423) adds a notebook to explain the functional interface.
- [#424](https://github.com/pytask-dev/pytask/pull/424) fixes problems with `~_pytask.path.import_path`.
- [#426](https://github.com/pytask-dev/pytask/pull/426) publishes the `pytask.tree_util` module.
- [#427](https://github.com/pytask-dev/pytask/pull/427) fixes type annotations for `pytask.PTask.depends_on` and
  `pytask.PTask.produces`.
- [#428](https://github.com/pytask-dev/pytask/pull/428) updates the example in the readme.
- [#429](https://github.com/pytask-dev/pytask/pull/429) implements a more informative error message when `node.state()` throws an
  exception. Now, it is easy to see which tasks are affected.
- [#430](https://github.com/pytask-dev/pytask/pull/430) updates some parts of the documentation.
- [#431](https://github.com/pytask-dev/pytask/pull/431) enables colors for WSL.
- [#432](https://github.com/pytask-dev/pytask/pull/432) fixes type checking of `pytask.mark.xxx`.
- [#433](https://github.com/pytask-dev/pytask/pull/433) fixes the ids generated for `pytask.PythonNode`s.
- [#437](https://github.com/pytask-dev/pytask/pull/437) fixes the detection of task functions and publishes
  `pytask.is_task_function`.
- [#438](https://github.com/pytask-dev/pytask/pull/438) clarifies some types.
- [#440](https://github.com/pytask-dev/pytask/pull/440) refines more types.
- [#441](https://github.com/pytask-dev/pytask/pull/441) updates more parts of the documentation.
- [#442](https://github.com/pytask-dev/pytask/pull/442) allows users to import `from pytask import mark` and use `@mark.skip`.

## 0.3.2 - 2023-06-07

- [#345](https://github.com/pytask-dev/pytask/pull/345) updates the version numbers in animations.
- [#352](https://github.com/pytask-dev/pytask/pull/352) publishes `db` that is required by pytask-environment.
- [#354](https://github.com/pytask-dev/pytask/pull/354) adds a `-f/--force` flag to execute tasks even though nothing may have
  changed.
- [#355](https://github.com/pytask-dev/pytask/pull/355) refactors a lot of things related to nodes.
- [#357](https://github.com/pytask-dev/pytask/pull/357) add hashing for task files to detect changes when modification times do
  not match.
- [#364](https://github.com/pytask-dev/pytask/pull/364) updates `update_plugin_list.py`.
- [#365](https://github.com/pytask-dev/pytask/pull/365) reworks the panel on the index page with sphinx-design.
- [#366](https://github.com/pytask-dev/pytask/pull/366) adds light and dark logos and fixes some warnings when building the
  documentation.
- [#369](https://github.com/pytask-dev/pytask/pull/369) fixes an error in `update_plugin_list.py` introduced by [#364](https://github.com/pytask-dev/pytask/pull/364).
- [#370](https://github.com/pytask-dev/pytask/pull/370) reverts the changes that turn `Node.state()` into a hook.
- [#371](https://github.com/pytask-dev/pytask/pull/371) renames `Node` to `MetaNode`.
- [#373](https://github.com/pytask-dev/pytask/pull/373) adds importing task modules to `sys.modules` and fully adopting pytest's
  importlib mode. Thanks to [@NickCrews](https://github.com/NickCrews). (Fixes [#374](https://github.com/pytask-dev/pytask/issues/374).)
- [#376](https://github.com/pytask-dev/pytask/pull/376) enhances the documentation for `pytask dag`.
- [#378](https://github.com/pytask-dev/pytask/pull/378) conditionally skips test on MacOS.
- [#381](https://github.com/pytask-dev/pytask/pull/381) deprecates `@pytask.mark.parametrize`. (Closes [#233](https://github.com/pytask-dev/pytask/issues/233).)
- [#501](https://github.com/pytask-dev/pytask/pull/501) removes `pytask.MetaNode`.

## 0.3.1 - 2023-12-25

- [#337](https://github.com/pytask-dev/pytask/pull/337) fixes fallback to root path when `pytask collect` or `pytask clean` are
  used without paths.

## 0.3.0 - 2023-12-22

- [#313](https://github.com/pytask-dev/pytask/pull/313) refactors the configuration. INI configurations are no longer supported.
- [#326](https://github.com/pytask-dev/pytask/pull/326) fixes the badge for status of the workflow.
- [#329](https://github.com/pytask-dev/pytask/pull/329) adds ruff to pre-commit hooks.
- [#330](https://github.com/pytask-dev/pytask/pull/330) add a guide for migrating from scripts to pytask.
- [#332](https://github.com/pytask-dev/pytask/pull/332) refactors `database.py`.
- [#333](https://github.com/pytask-dev/pytask/pull/333) requires attrs v21.3.0 and updates the code accordingly.
- [#334](https://github.com/pytask-dev/pytask/pull/334) adds `target-version` to ruff config.

## 0.2.7 - 2022-12-14

- [#307](https://github.com/pytask-dev/pytask/pull/307) adds Python 3.11 to the CI.
- [#308](https://github.com/pytask-dev/pytask/pull/308) replaces pydot with pygraphviz.
- [#311](https://github.com/pytask-dev/pytask/pull/311) fixes a link in the documentation.
- [#311](https://github.com/pytask-dev/pytask/pull/311) adds refurb to pre-commit hooks.
- [#318](https://github.com/pytask-dev/pytask/pull/318) clarifies an example on nested dependencies and products.
- [#321](https://github.com/pytask-dev/pytask/pull/321) converts more choice options to enums.
- [#322](https://github.com/pytask-dev/pytask/pull/322) replaces SVGs with animations by termynal.
- [#325](https://github.com/pytask-dev/pytask/pull/325) allows to collect dynamically created tasks.

## 0.2.6 - 2022-10-27

- [#297](https://github.com/pytask-dev/pytask/pull/297) moves non-hook functions from `warnings.py` to `warnings_utils.py` and
  publishes them so that pytask-parallel can import them.
- [#305](https://github.com/pytask-dev/pytask/pull/305) removes traces of colorama. Whatever it did should be handled by rich.

## 0.2.5 - 2022-08-02

- [#288](https://github.com/pytask-dev/pytask/pull/288) fixes pinning pybaum to v0.1.1 or a version that supports `tree_yield()`.
- [#289](https://github.com/pytask-dev/pytask/pull/289) shortens the task ids when using `pytask collect`. Fixes [#286](https://github.com/pytask-dev/pytask/issues/286).
- [#290](https://github.com/pytask-dev/pytask/pull/290) implements a dry-run with `pytask --dry-run` to see which tasks would be
  executed.
- [#296](https://github.com/pytask-dev/pytask/pull/296) fixes a bug where the source code of the wrapped function could not be
  retrieved.

## 0.2.4 - 2022-06-28

- [#279](https://github.com/pytask-dev/pytask/pull/279) enhances some tutorials with spell and grammar checking.
- [#282](https://github.com/pytask-dev/pytask/pull/282) updates the tox configuration.
- [#283](https://github.com/pytask-dev/pytask/pull/283) fixes an issue with coverage and tests using pexpect + `pdb.set_trace()`.
- [#285](https://github.com/pytask-dev/pytask/pull/285) implements that pytask does not show the traceback of tasks that are
  skipped because their previous task failed. Fixes [#284](https://github.com/pytask-dev/pytask/issues/284).
- [#287](https://github.com/pytask-dev/pytask/pull/287) changes that all files that are not produced by a task are displayed in
  the error message. Fixes [#262](https://github.com/pytask-dev/pytask/issues/262).

## 0.2.3 - 2022-05-30

- [#276](https://github.com/pytask-dev/pytask/pull/276) fixes `pytask clean` when git is not installed. Fixes [#275](https://github.com/pytask-dev/pytask/issues/275).
- [#277](https://github.com/pytask-dev/pytask/pull/277) ignores `DeprecationWarning` and `PendingDeprecationWarning` by default.
  Previously, they were enabled, but they should be shown when testing the project with
  pytest, not after the execution with pytask. Fixes [#269](https://github.com/pytask-dev/pytask/issues/269).
- [#278](https://github.com/pytask-dev/pytask/pull/278) counts multiple occurrences of a warning instead of listing the module or
  task name again and again. Fixes [#270](https://github.com/pytask-dev/pytask/issues/270).

## 0.2.2 - 2022-05-14

- [#267](https://github.com/pytask-dev/pytask/pull/267) fixes the info under the live execution table to show the total number of
  tasks also for pytask-parallel.
- [#273](https://github.com/pytask-dev/pytask/pull/273) reworks `pytask clean` so that it ignores files tracked by git. Resolves
  [#146](https://github.com/pytask-dev/pytask/issues/146).

## 0.2.1 - 2022-04-28

- [#259](https://github.com/pytask-dev/pytask/pull/259) adds an `.svg` for profiling tasks.
- [#261](https://github.com/pytask-dev/pytask/pull/261) adds a config file option to sort entries in live table
- [#262](https://github.com/pytask-dev/pytask/pull/262) allows pytask to capture warnings. Here is the
  [guide](https://pytask-dev.readthedocs.io/en/stable/how_to_guides/capture_warnings.html).

## 0.2.0 - 2022-04-14

- [#211](https://github.com/pytask-dev/pytask/pull/211) allows for flexible dependencies and products which can be any pytree of
  native Python objects as supported by pybaum.
- [#227](https://github.com/pytask-dev/pytask/pull/227) implements `task.kwargs` as a new way for a task to hold parametrized
  arguments. It also implements `_pytask.models.CollectionMetadata` to carry
  parametrized arguments to the task class.
- [#228](https://github.com/pytask-dev/pytask/pull/228) removes `task.pytaskmark` and moves the information to
  `pytask.CollectionMetadata.markers`.
- [#229](https://github.com/pytask-dev/pytask/pull/229) implements a new loop-based approach to parametrizations using the
  `@pytask.mark.task` decorator.
- [#230](https://github.com/pytask-dev/pytask/pull/230) implements `_pytask.logging._TimeUnit` as a
  `typing.NamedTuple` for better typing.
- [#232](https://github.com/pytask-dev/pytask/pull/232) moves the documentation to MyST.
- [#234](https://github.com/pytask-dev/pytask/pull/234) removes `MetaTask`. There is only `pytask.Task`.
- [#235](https://github.com/pytask-dev/pytask/pull/235) refactors the utility functions for dealing with marks in
  `_pytask.mark_utils`. (Closes [#220](https://github.com/pytask-dev/pytask/issues/220).)
- [#236](https://github.com/pytask-dev/pytask/pull/236) refactors `_pytask.collect` and places shared functions in
  `_pytask.collect_utils`.
- [#237](https://github.com/pytask-dev/pytask/pull/237) publish more functions.
- [#238](https://github.com/pytask-dev/pytask/pull/238) allows any order of decorators with a `@pytask.mark.task` decorator.
- [#239](https://github.com/pytask-dev/pytask/pull/239) adds a warning on globals for parametrizations and some fixes.
- [#241](https://github.com/pytask-dev/pytask/pull/241) allows parametrizing over single dicts.
- [#242](https://github.com/pytask-dev/pytask/pull/242) removes tasks from global `_pytask.task_utils.COLLECTED_TASKS` to
  avoid re-collection when the programmatic interface is used.
- [#243](https://github.com/pytask-dev/pytask/pull/243) converts choice options to use enums instead of simple strings.
- [#245](https://github.com/pytask-dev/pytask/pull/245) adds choices on the command line to the help pages as metavars and show
  defaults.
- [#246](https://github.com/pytask-dev/pytask/pull/246) formalizes choices for `click.Choice` to `enum.Enum`.
- [#252](https://github.com/pytask-dev/pytask/pull/252) adds a counter at the bottom of the execution table to show how many tasks
  have been processed.
- [#253](https://github.com/pytask-dev/pytask/pull/253) adds support for `pyproject.toml`.
- [#254](https://github.com/pytask-dev/pytask/pull/254) improves test coverage, fixes a bug, and improves the deprecation message
  for the configuration.
- [#255](https://github.com/pytask-dev/pytask/pull/255) converts the readme to markdown and multiple pngs to svgs.
- [#256](https://github.com/pytask-dev/pytask/pull/256) adds even more svgs and scripts to generate them to the documentation and
  other improvements.

## 0.1.9 - 2022-02-23

- [#197](https://github.com/pytask-dev/pytask/pull/197) publishes types, and adds classes and functions to the main namespace.
- [#217](https://github.com/pytask-dev/pytask/pull/217) enhances the tutorial on how to set up a project.
- [#218](https://github.com/pytask-dev/pytask/pull/218) removes `depends_on` and `produces` from the task function when parsed.
- [#219](https://github.com/pytask-dev/pytask/pull/219) removes some leftovers from pytest in `_pytask.mark.Mark`.
- [#221](https://github.com/pytask-dev/pytask/pull/221) adds more test cases for parametrizations.
- [#222](https://github.com/pytask-dev/pytask/pull/222) adds an automated Github Actions job for creating a list pytask plugins.
- [#225](https://github.com/pytask-dev/pytask/pull/225) fixes a circular import noticeable in plugins created by [#197](https://github.com/pytask-dev/pytask/pull/197).
- [#226](https://github.com/pytask-dev/pytask/pull/226) fixes a bug where the number of items in the live table during the
  execution is not exhausted. (Closes [#223](https://github.com/pytask-dev/pytask/issues/223).)

## 0.1.8 - 2022-02-07

- [#210](https://github.com/pytask-dev/pytask/pull/210) allows `__tracebackhide__` to be a callable that accepts the current
  exception as an input. Closes [#145](https://github.com/pytask-dev/pytask/issues/145).
- [#213](https://github.com/pytask-dev/pytask/pull/213) improves coverage and reporting.
- [#215](https://github.com/pytask-dev/pytask/pull/215) makes the help pages of the CLI prettier.

## 0.1.7 - 2022-01-28

- [#153](https://github.com/pytask-dev/pytask/pull/153) adds support for Python 3.10 which requires pony >= 0.7.15.
- [#192](https://github.com/pytask-dev/pytask/pull/192) deprecates Python 3.6.
- [#209](https://github.com/pytask-dev/pytask/pull/209) cancels previous CI jobs when a new job is started.

## 0.1.6 - 2022-01-27

- [#191](https://github.com/pytask-dev/pytask/pull/191) adds a guide on how to profile pytask to the developer's guide.
- [#192](https://github.com/pytask-dev/pytask/pull/192) deprecates Python 3.6.
- [#193](https://github.com/pytask-dev/pytask/pull/193) adds more figures to the documentation.
- [#194](https://github.com/pytask-dev/pytask/pull/194) updates the `README.rst`.
- [#196](https://github.com/pytask-dev/pytask/pull/196) references the two new cookiecutters for projects and plugins.
- [#198](https://github.com/pytask-dev/pytask/pull/198) fixes the documentation of
  `@pytask.mark.skipif`. (Closes [#195](https://github.com/pytask-dev/pytask/issues/195))
- [#199](https://github.com/pytask-dev/pytask/pull/199) extends the error message when paths are ambiguous on case-insensitive
  file systems.
- [#200](https://github.com/pytask-dev/pytask/pull/200) implements the `@pytask.mark.task` decorator to
  mark functions as tasks regardless of whether they are prefixed with `task_` or not.
- [#201](https://github.com/pytask-dev/pytask/pull/201) adds tests for `_pytask.mark_utils`.
- [#204](https://github.com/pytask-dev/pytask/pull/204) removes internal traceback frames from exceptions raised somewhere in
  pytask.
- [#208](https://github.com/pytask-dev/pytask/pull/208) fixes the best practices guide for parametrizations.
- [#209](https://github.com/pytask-dev/pytask/pull/209) cancels previous CI runs automatically.
- [#212](https://github.com/pytask-dev/pytask/pull/212) add `.coveragerc` and improve coverage.

## 0.1.5 - 2022-01-10

- [#184](https://github.com/pytask-dev/pytask/pull/184) refactors `_pytask.shared.reduce_node_name` and shorten task names
  in many places.
- [#185](https://github.com/pytask-dev/pytask/pull/185) fix issues with drawing a graph and adds the `--rank-direction` to change
  the direction of the DAG.
- [#186](https://github.com/pytask-dev/pytask/pull/186) enhance live displays by deactivating auto-refresh, among other things.
- [#187](https://github.com/pytask-dev/pytask/pull/187) allows to enable and disable showing tracebacks and potentially different
  styles in the future with `show_traceback=True|False`.
- [#188](https://github.com/pytask-dev/pytask/pull/188) refactors some code related to `pytask.ExitCode`.
- [#189](https://github.com/pytask-dev/pytask/pull/189) do not display a table in the execution if no task was run.
- [#190](https://github.com/pytask-dev/pytask/pull/190) updates the release notes.

## 0.1.4 - 2022-01-04

- [#153](https://github.com/pytask-dev/pytask/pull/153) adds support and testing for Python 3.10.
- [#159](https://github.com/pytask-dev/pytask/pull/159) removes files for creating a conda package which is handled by
  conda-forge.
- [#160](https://github.com/pytask-dev/pytask/pull/160) adds rudimentary typing to pytask.
- [#161](https://github.com/pytask-dev/pytask/pull/161) removes a workaround for pyreadline which is also removed in pytest 7.
- [#163](https://github.com/pytask-dev/pytask/pull/163) allow forward slashes in expressions and marker expressions.
- [#164](https://github.com/pytask-dev/pytask/pull/164) allows to use backward slashes in expressions and marker expressions.
- [#167](https://github.com/pytask-dev/pytask/pull/167) makes small changes to the docs.
- [#172](https://github.com/pytask-dev/pytask/pull/172) embeds URLs in task ids. See `editor_url_scheme` for more
  information.
- [#173](https://github.com/pytask-dev/pytask/pull/173) replaces `ColorCode` with custom rich themes.
- [#174](https://github.com/pytask-dev/pytask/pull/174) restructures loosely defined outcomes to clear `enum.Enum`.
- [#176](https://github.com/pytask-dev/pytask/pull/176) and [#177](https://github.com/pytask-dev/pytask/pull/177) implement a summary panel that holds aggregate information
  about the number of successes, fails and other status.
- [#178](https://github.com/pytask-dev/pytask/pull/178) adds stylistic changes like reducing tasks ids even more and dimming the
  path part.
- [#180](https://github.com/pytask-dev/pytask/pull/180) fixes parsing relative paths from the configuration file.
- [#181](https://github.com/pytask-dev/pytask/pull/181) adds correct formatting of running tasks.
- [#182](https://github.com/pytask-dev/pytask/pull/182) introduces that only the starting year is displayed in the license
  following <https://hynek.me/til/copyright-years>.
- [#183](https://github.com/pytask-dev/pytask/pull/183) enables tracing down the source of a function through decorators.

## 0.1.3 - 2021-11-30

- [#157](https://github.com/pytask-dev/pytask/pull/157) adds packaging to the dependencies of the package.
- [#158](https://github.com/pytask-dev/pytask/pull/158) converts time units to the nearest integer.

## 0.1.2 - 2021-11-27

- [#135](https://github.com/pytask-dev/pytask/pull/135) implements handling of version in docs as proposed by setuptools-scm.
- [#142](https://github.com/pytask-dev/pytask/pull/142) removes the display of skipped and persisted tasks from the live execution
  table for the default verbosity level of 1. They are displayed at 2.
- [#144](https://github.com/pytask-dev/pytask/pull/144) adds tryceratops to the pre-commit hooks for catching issues with
  exceptions.
- [#151](https://github.com/pytask-dev/pytask/pull/151) adds a limit on the number of items displayed in the execution table which
  is configurable with `n_entries_in_table` in the configuration file.
- [#152](https://github.com/pytask-dev/pytask/pull/152) makes the duration of the execution readable by humans by separating it
  into days, hours, minutes and seconds.
- [#155](https://github.com/pytask-dev/pytask/pull/155) implements functions to check for optional packages and programs and
  raises errors for requirements to draw the DAG earlier.
- [#156](https://github.com/pytask-dev/pytask/pull/156) adds the option `show_errors_immediately` to print/show errors as
  soon as they occur. Resolves [#150](https://github.com/pytask-dev/pytask/issues/150).

## 0.1.1 - 2021-08-25

- [#138](https://github.com/pytask-dev/pytask/pull/138) changes the default `verbosity` to `1` which displays the live table
  during execution and `0` display the symbols for outcomes (e.g. `.`, `F`, `s`).
- [#139](https://github.com/pytask-dev/pytask/pull/139) enables rich's auto-refresh mechanism for live objects which causes almost
  no performance penalty for the live table compared to the symbolic output.

## 0.1.0 - 2021-07-20

- [#106](https://github.com/pytask-dev/pytask/pull/106) implements a verbose mode for the execution which is available with
  `pytask -v` and shows a table with running and completed tasks. It also refines the
  collection status.
- [#116](https://github.com/pytask-dev/pytask/pull/116), [#117](https://github.com/pytask-dev/pytask/pull/117), and [#123](https://github.com/pytask-dev/pytask/pull/123) fix [#104](https://github.com/pytask-dev/pytask/issues/104) which prevented to skip
  tasks with missing dependencies.
- [#118](https://github.com/pytask-dev/pytask/pull/118) makes the path to the configuration in the session header os-specific.
- [#119](https://github.com/pytask-dev/pytask/pull/119) changes that when marker or keyword expressions are used to select tasks,
  also the predecessors of the selected tasks will be executed.
- [#120](https://github.com/pytask-dev/pytask/pull/120) implements that a single `KeyboardInterrupt` stops the execution and
  previously collected reports are shown. Fixes [#111](https://github.com/pytask-dev/pytask/issues/111).
- [#121](https://github.com/pytask-dev/pytask/pull/121) add skipped and persisted tasks to the execution footer.
- [#127](https://github.com/pytask-dev/pytask/pull/127) make the table during execution the default. Silence pytask with negative
  verbose mode integers and increase verbosity with positive ones.
- [#129](https://github.com/pytask-dev/pytask/pull/129) allows to hide frames from the traceback by using
  `__tracebackhide__ = True`.
- [#130](https://github.com/pytask-dev/pytask/pull/130) enables rendering of tracebacks from subprocesses with rich.

## 0.0.16 - 2021-06-25

- [#113](https://github.com/pytask-dev/pytask/pull/113) fixes error when using `pytask --version` with click v8.

## 0.0.15 - 2021-06-24

- [#80](https://github.com/pytask-dev/pytask/pull/80) replaces some remaining formatting using `pprint` with `rich`.
- [#81](https://github.com/pytask-dev/pytask/pull/81) adds a warning if a path is not correctly cased on a case-insensitive file
  system. This facilitates cross-platform builds of projects. Deactivate the check by
  setting `check_casing_of_paths = false` in the configuration file. See
  `check_casing_of_paths` for more information.
- [#83](https://github.com/pytask-dev/pytask/pull/83) replaces `versioneer` with `setuptools_scm`.
- [#84](https://github.com/pytask-dev/pytask/pull/84) fixes an error in the path normalization introduced by [#81](https://github.com/pytask-dev/pytask/pull/81).
- [#85](https://github.com/pytask-dev/pytask/pull/85) sorts collected tasks, dependencies, and products by name.
- [#87](https://github.com/pytask-dev/pytask/pull/87) fixes that dirty versions are displayed in the documentation.
- [#88](https://github.com/pytask-dev/pytask/pull/88) adds the `pytask profile` command to show information on tasks like
  duration and file size of products.
- [#93](https://github.com/pytask-dev/pytask/pull/93) fixes the display of parametrized arguments in the console.
- [#94](https://github.com/pytask-dev/pytask/pull/94) adds `show_locals` which allows to print local variables in
  tracebacks.
- [#96](https://github.com/pytask-dev/pytask/pull/96) implements a spinner to show the progress during the collection.
- [#99](https://github.com/pytask-dev/pytask/pull/99) enables color support in WSL and fixes `show_locals` during
  collection.
- [#101](https://github.com/pytask-dev/pytask/pull/101) implement to visualize the project's DAG. [#108](https://github.com/pytask-dev/pytask/pull/108) refines the
  implementation.
- [#102](https://github.com/pytask-dev/pytask/pull/102) adds an example if a parametrization provides not the number of arguments
  specified in the signature.
- [#105](https://github.com/pytask-dev/pytask/pull/105) simplifies the logging of the tasks.
- [#107](https://github.com/pytask-dev/pytask/pull/107) adds and new hook `_pytask.hookspecs.pytask_unconfigure` which
  makes pytask return `pdb.set_trace` at the end of a session which allows to use
  `breakpoint` inside test functions using pytask.
- [#109](https://github.com/pytask-dev/pytask/pull/109) makes pytask require networkx>=2.4 since previous versions fail with
  Python 3.9.
- [#110](https://github.com/pytask-dev/pytask/pull/110) adds a "New Features" section to the `README.rst`.

## 0.0.14 - 2021-03-23

- [#74](https://github.com/pytask-dev/pytask/pull/74) reworks the formatting of the command line output by using `rich`. Due to
  the new dependency, support for pytask with Python \<3.6.1 on PyPI and with Python
  \<3.7 on Anaconda will end.
- [#76](https://github.com/pytask-dev/pytask/pull/76) fixes [#75](https://github.com/pytask-dev/pytask/issues/75) which reports a bug when a closest ancestor cannot be
  found to shorten node names in the CLI output. Instead a common ancestor is used.

## 0.0.13 - 2021-03-09

- [#72](https://github.com/pytask-dev/pytask/pull/72) adds conda-forge to the README and highlights importance of specifying
  dependencies and products.
- [#62](https://github.com/pytask-dev/pytask/pull/62) implements the `pytask.mark.skipif` marker to conditionally skip
  tasks. Many thanks to [@roecla](https://github.com/roecla) for implementing this feature and a warm welcome
  since she is the first pytask contributor!

## 0.0.12 - 2021-02-27

- [#55](https://github.com/pytask-dev/pytask/pull/55) implements miscellaneous fixes to improve error message, tests and
  coverage.
- [#59](https://github.com/pytask-dev/pytask/pull/59) adds a tutorial on using plugins and features plugins more prominently.
- [#60](https://github.com/pytask-dev/pytask/pull/60) adds the MIT license to the project and mentions pytest and its developers.
- [#61](https://github.com/pytask-dev/pytask/pull/61) adds many changes to the documentation.
- [#65](https://github.com/pytask-dev/pytask/pull/65) adds versioneer to pytask and [#66](https://github.com/pytask-dev/pytask/pull/66) corrects the coverage reports
  which were deflated due to the new files.
- [#67](https://github.com/pytask-dev/pytask/pull/67) prepares pytask to be published on PyPI and [#68](https://github.com/pytask-dev/pytask/pull/68) fixes the pipeline,
  and [#69](https://github.com/pytask-dev/pytask/pull/69) prepares releasing v0.0.12 and adds new shields.

## 0.0.11 - 2020-12-27

- [#45](https://github.com/pytask-dev/pytask/pull/45) adds the option to stop execution after a number of tasks has failed.
  Closes [#44](https://github.com/pytask-dev/pytask/issues/44).
- [#47](https://github.com/pytask-dev/pytask/pull/47) reduce node names in error messages while resolving dependencies.
- [#49](https://github.com/pytask-dev/pytask/pull/49) starts a style guide for pytask.
- [#50](https://github.com/pytask-dev/pytask/pull/50) implements correct usage of singular and plural in collection logs.
- [#51](https://github.com/pytask-dev/pytask/pull/51) allows to invoke pytask through the Python interpreter with
  `python -m pytask` which will add the current path to `sys.path`.
- [#52](https://github.com/pytask-dev/pytask/pull/52) allows to prioritize tasks with `pytask.mark.try_last` and
  `pytask.mark.try_first`.
- [#53](https://github.com/pytask-dev/pytask/pull/53) changes the theme of the documentation to furo.
- [#54](https://github.com/pytask-dev/pytask/pull/54) releases v0.0.11.

## 0.0.10 - 2020-11-18

- [#40](https://github.com/pytask-dev/pytask/pull/40) cleans up the capture manager and other parts of pytask.
- [#41](https://github.com/pytask-dev/pytask/pull/41) shortens the task ids in the error reports for better readability.
- [#42](https://github.com/pytask-dev/pytask/pull/42) ensures that lists with one element and dictionaries with only a zero key
  as input for `@pytask.mark.depends_on` and `@pytask.mark.produces` are preserved as a
  dictionary inside the function.

## 0.0.9 - 2020-10-28

- [#31](https://github.com/pytask-dev/pytask/pull/31) adds `pytask collect` to show information on collected tasks.
- [#32](https://github.com/pytask-dev/pytask/pull/32) fixes `pytask clean`.
- [#33](https://github.com/pytask-dev/pytask/pull/33) adds a module to apply common parameters to the command line interface.
- [#34](https://github.com/pytask-dev/pytask/pull/34) skips `pytask_collect_task_teardown` if task is None.
- [#35](https://github.com/pytask-dev/pytask/pull/35) adds the ability to capture stdout and stderr with the CaptureManager.
- [#36](https://github.com/pytask-dev/pytask/pull/36) reworks the debugger to make it work with the CaptureManager.
- [#37](https://github.com/pytask-dev/pytask/pull/37) removes `reports` argument from hooks related to task collection.
- [#38](https://github.com/pytask-dev/pytask/pull/38) allows to pass dictionaries as dependencies and products and inside the
  function `depends_on` and `produces` become dictionaries.
- [#39](https://github.com/pytask-dev/pytask/pull/39) releases v0.0.9.

## 0.0.8 - 2020-10-04

- [#30](https://github.com/pytask-dev/pytask/pull/30) fixes or adds the session object to some hooks which was missing from the
  previous release.

## 0.0.7 - 2020-10-03

- [#25](https://github.com/pytask-dev/pytask/pull/25) allows to customize the names of the task files.
- [#26](https://github.com/pytask-dev/pytask/pull/26) makes commands return the correct exit codes.
- [#27](https://github.com/pytask-dev/pytask/pull/27) implements the `pytask_collect_task_teardown` hook specification to perform
  checks after a task is collected.
- [#28](https://github.com/pytask-dev/pytask/pull/28) implements the `@pytask.mark.persist` decorator.
- [#29](https://github.com/pytask-dev/pytask/pull/29) releases 0.0.7.

## 0.0.6 - 2020-09-12

- [#16](https://github.com/pytask-dev/pytask/pull/16) reduces the traceback generated from tasks, failure section in report, fix
  error passing a file path to pytask, add demo to README.
- [#17](https://github.com/pytask-dev/pytask/pull/17) changes the interface to subcommands, adds `"-c/--config"` option to pass a
  path to a configuration file and adds `pytask clean` ([#22](https://github.com/pytask-dev/pytask/pull/22) as well), a command
  to clean your project.
- [#18](https://github.com/pytask-dev/pytask/pull/18) changes the documentation theme to alabaster.
- [#19](https://github.com/pytask-dev/pytask/pull/19) adds some changes related to ignored folders.
- [#20](https://github.com/pytask-dev/pytask/pull/20) fixes copying code examples in the documentation.
- [#21](https://github.com/pytask-dev/pytask/pull/21) enhances the ids generated by parametrization, allows to change them via
  the `ids` argument, and adds tutorials.
- [#23](https://github.com/pytask-dev/pytask/pull/23) allows to specify paths via the configuration file, documents the cli and
  configuration options.
- [#24](https://github.com/pytask-dev/pytask/pull/24) releases 0.0.6.

## 0.0.5 - 2020-08-12

- [#10](https://github.com/pytask-dev/pytask/pull/10) turns parametrization into a plugin.
- [#11](https://github.com/pytask-dev/pytask/pull/11) extends the documentation.
- [#12](https://github.com/pytask-dev/pytask/pull/12) replaces `pytest.mark` with `pytask.mark`.
- [#13](https://github.com/pytask-dev/pytask/pull/13) implements selecting tasks via expressions or marker expressions.
- [#14](https://github.com/pytask-dev/pytask/pull/14) separates the namespace of pytask to `pytask` and `_pytask`.
- [#15](https://github.com/pytask-dev/pytask/pull/15) implements better tasks ids which consists of
  \<path-to-task-file>::\<func-name> and are certainly unique. And, it releases 0.0.5.

## 0.0.4 - 2020-07-22

- [#9](https://github.com/pytask-dev/pytask/pull/9) adds hook specifications to the parametrization of tasks which allows
  `pytask-latex` and `pytask-r` to pass different command line arguments to a
  parametrized task and its script. Also, it prepares the release of 0.0.4.

## 0.0.3 - 2020-07-19

- [#7](https://github.com/pytask-dev/pytask/pull/7) makes pytask exit with code 1 if a task failed and the
  `skip_ancestor_failed` decorator is only applied to descendant tasks not the task
  itself.
- [#8](https://github.com/pytask-dev/pytask/pull/8) releases v0.0.3

## 0.0.2 - 2020-07-17

- [#2](https://github.com/pytask-dev/pytask/pull/2) provided multiple small changes.
- [#3](https://github.com/pytask-dev/pytask/pull/3) implements a class which holds the execution report of one task.
- [#4](https://github.com/pytask-dev/pytask/pull/4) makes adjustments after moving to `main` as the default branch.
- [#5](https://github.com/pytask-dev/pytask/pull/5) adds `pytask_add_hooks` to add more hook specifications and register hooks.
- [#6](https://github.com/pytask-dev/pytask/pull/6) releases v0.0.2.

## 0.0.1 - 2020-06-29

- [#1](https://github.com/pytask-dev/pytask/pull/1) combined the whole effort which went into releasing v0.0.1.
