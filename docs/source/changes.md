# Changes

The document records all past pytask releases and what went into them in reverse
chronological order. Releases follow [semantic versioning](https://semver.org/) and all
releases are available on [PyPI](https://pypi.org/project/pytask) and
[Anaconda.org](https://anaconda.org/conda-forge/pytask).

## 0.4.3 - 2023-11-xx

- {pull}`483` simplifies the teardown of a task.
- {pull}`484` raises more informative error when directories instead of files are used
  with path nodes.
- {pull}`485` adds missing steps to unconfigure pytask after the job is done which
  caused flaky tests.
- {pull}`486` adds default names to {class}`~pytask.PPathNode`.
- {pull}`488` raises an error when an invalid value is used in a return annotation.
- {pull}`489` and {pull}`491` simplifies parsing products and does not raise an error
  when a product annotation is used with the argument name `produces`. And, allow
  `produces` to intake any node.
- {pull}`490` refactors and better tests parsing of dependencies.
- {pull}`496` makes pytask even lazier. Now, when a task produces a node whose hash
  remains the same, the consecutive tasks are not executed. It remained from when pytask
  relied on timestamps.
- {pull}`497` removes unnecessary code in the collection of tasks.

## 0.4.2 - 2023-11-08

- {pull}`449` simplifies the code building the plugin manager.
- {pull}`451` improves `collect_command.py` and renames `graph.py` to `dag_command.py`.
- {pull}`454` removes more `.svg`s and replaces them with animations.
- {pull}`455` adds more explanation when {meth}`~pytask.PNode.load` fails during the
  execution.
- {pull}`456` refers to the source code on Github when clicking on a source link.
- {pull}`457` refactors everything around formatting node names.
- {pull}`459` adds a pre-commit hook to sort `__all__`.
- {pull}`460` simplifies removing internal tracebacks from exceptions with a cause.
- {pull}`463` raise error when a task function is not defined inside the loop body.
- {pull}`464` improves pinned dependencies.
- {pull}`465` adds test to ensure internal tracebacks are removed by reports.
- {pull}`466` implements hashing for files instead of modification timestamps.
- {pull}`470` moves `.pytask.sqlite3` to `.pytask`.
- {pull}`472` adds `is_product` to {meth}`PNode.load`.
- {pull}`473` adds signatures to nodes which decouples an identifier from a name.
- {pull}`477` updates the PyPI action.
- {pull}`478` replaces black with ruff-format.
- {pull}`479` gives skips a higher precedence as an outcome than ancestor failed.
- {pull}`480` removes the check for missing root nodes from the generation of the DAG.
  It is delegated to the check during the execution.
- {pull}`481` improves coverage.
- {pull}`482` correctly handles names and signatures of {class}`~pytask.PythonNode`.

## 0.4.1 - 2023-10-11

- {pull}`443` ensures that `PythonNode.name` is always unique by only handling it
  internally.
- {pull}`444` moves all content of `setup.cfg` to `pyproject.toml`.
- {pull}`446` refactors `create_name_of_python_node` and fixes `PythonNode`s as returns.
- {pull}`447` simplifies the `tree_map` code while generating the DAG.
- {pull}`448` fixes handling multiple product annotations of a task.

## 0.4.0 - 2023-10-07

- {pull}`323` remove Python 3.7 support and use a new Github action to provide mamba.
- {pull}`384` allows to parse dependencies from every function argument if `depends_on`
  is not present.
- {pull}`387` replaces pony with sqlalchemy.
- {pull}`391` removes `@pytask.mark.parametrize`.
- {pull}`394` allows to add products with {obj}`typing.Annotation` and
  {obj}`~pytask.Product`.
- {pull}`395` refactors all occurrences of pybaum to {mod}`_pytask.tree_util`.
- {pull}`396` replaces pybaum with optree and adds paths to the name of
  {class}`pytask.PythonNode`'s allowing for better hashing.
- {pull}`397` adds support for {class}`typing.NamedTuple` and attrs classes in
  `@pytask.mark.task(kwargs=...)`.
- {pull}`398` deprecates the decorators `@pytask.mark.depends_on` and
  `@pytask.mark.produces`.
- {pull}`402` replaces ABCs with protocols allowing for more flexibility for users
  implementing their own nodes.
- {pull}`404` allows to use function returns to define task products.
- {pull}`406` allows to match function returns to node annotations with prefix trees.
- {pull}`408` removes `.value` from `Node` protocol.
- {pull}`409` make `.from_annot` an optional feature of nodes.
- {pull}`410` allows to pass functions to `PythonNode(hash=...)`.
- {pull}`411` implements a new functional interface and adds experimental support for
  defining and running tasks in REPLs or Jupyter notebooks.
- {pull}`412` adds protocols for tasks.
- {pull}`413` removes scripts to generate `.svg`s.
- {pull}`414` allow more ruff rules.
- {pull}`416` removes `.from_annot` again.
- {pull}`417` deprecates {func}`pytask.mark.task` in favor of {func}`pytask.task`.
- {pull}`418` fixes and error and simplifies code in `dag.py`.
- {pull}`420` converts `DeprecationWarning`s to `FutureWarning`s for the deprecated
  decorators.
- {pull}`421` removes the deprecation warning when `produces` is used as an magic
  function keyword to define products.
- {pull}`423` adds a notebook to explain the functional interface.
- {pull}`424` fixes problems with {func}`~_pytask.path.import_path`.
- {pull}`426` publishes the {mod}`pytask.tree_util` module.
- {pull}`427` fixes type annotations for {attr}`pytask.PTask.depends_on` and
  {attr}`pytask.PTask.produces`.
- {pull}`428` updates the example in the readme.
- {pull}`429` implements a more informative error message when `node.state()` throws an
  exception. Now, it is easy to see which tasks are affected.
- {pull}`430` updates some parts of the documentation.
- {pull}`431` enables colors for WSL.
- {pull}`432` fixes type checking of `pytask.mark.xxx`.
- {pull}`433` fixes the ids generated for {class}`~pytask.PythonNode`s.
- {pull}`437` fixes the detection of task functions and publishes
  {func}`pytask.is_task_function`.
- {pull}`438` clarifies some types.
- {pull}`440` refines more types.
- {pull}`441` updates more parts of the documentation.
- {pull}`442` allows users to import `from pytask import mark` and use `@mark.skip`.

## 0.3.2 - 2023-06-07

- {pull}`345` updates the version numbers in animations.
- {pull}`352` publishes `db` that is required by pytask-environment.
- {pull}`354` adds a `-f/--force` flag to execute tasks even though nothing may have
  changed.
- {pull}`355` refactors a lot of things related to nodes.
- {pull}`357` add hashing for task files to detect changes when modification times do
  not match.
- {pull}`364` updates `update_plugin_list.py`.
- {pull}`365` reworks the panel on the index page with sphinx-design.
- {pull}`366` adds light and dark logos and fixes some warnings when building the
  documentation.
- {pull}`369` fixes an error in `update_plugin_list.py` introduced by {pull}`364`.
- {pull}`370` reverts the changes that turn `Node.state()` into a hook.
- {pull}`371` renames `Node` to `MetaNode`.
- {pull}`373` adds importing task modules to `sys.modules` and fully adopting pytest's
  importlib mode. Thanks to {user}`NickCrews`. (Fixes {issue}`374`.)
- {pull}`376` enhances the documentation for `pytask dag`.
- {pull}`378` conditionally skips test on MacOS.
- {pull}`381` deprecates `@pytask.mark.parametrize`. (Closes {issue}`233`.)

## 0.3.1 - 2023-12-25

- {pull}`337` fixes fallback to root path when `pytask collect` or `pytask clean` are
  used without paths.

## 0.3.0 - 2023-12-22

- {pull}`313` refactors the configuration. INI configurations are no longer supported.
- {pull}`326` fixes the badge for status of the workflow.
- {pull}`329` adds ruff to pre-commit hooks.
- {pull}`330` add a guide for migrating from scripts to pytask.
- {pull}`332` refactors `database.py`.
- {pull}`333` requires attrs v21.3.0 and updates the code accordingly.
- {pull}`334` adds `target-version` to ruff config.

## 0.2.7 - 2022-12-14

- {pull}`307` adds Python 3.11 to the CI.
- {pull}`308` replaces pydot with pygraphviz.
- {pull}`311` fixes a link in the documentation.
- {pull}`311` adds refurb to pre-commit hooks.
- {pull}`318` clarifies an example on nested dependencies and products.
- {pull}`321` converts more choice options to enums.
- {pull}`322` replaces SVGs with animations by termynal.
- {pull}`325` allows to collect dynamically created tasks.

## 0.2.6 - 2022-10-27

- {pull}`297` moves non-hook functions from `warnings.py` to `warnings_utils.py` and
  publishes them so that pytask-parallel can import them.
- {pull}`305` removes traces of colorama. Whatever it did should be handled by rich.

## 0.2.5 - 2022-08-02

- {pull}`288` fixes pinning pybaum to v0.1.1 or a version that supports `tree_yield()`.
- {pull}`289` shortens the task ids when using `pytask collect`. Fixes {issue}`286`.
- {pull}`290` implements a dry-run with `pytask --dry-run` to see which tasks would be
  executed.
- {pull}`296` fixes a bug where the source code of the wrapped function could not be
  retrieved.

## 0.2.4 - 2022-06-28

- {pull}`279` enhances some tutorials with spell and grammar checking.
- {pull}`282` updates the tox configuration.
- {pull}`283` fixes an issue with coverage and tests using pexpect + `pdb.set_trace()`.
- {pull}`285` implements that pytask does not show the traceback of tasks that are
  skipped because their previous task failed. Fixes {issue}`284`.
- {pull}`287` changes that all files that are not produced by a task are displayed in
  the error message. Fixes {issue}`262`.

## 0.2.3 - 2022-05-30

- {pull}`276` fixes `pytask clean` when git is not installed. Fixes {issue}`275`.
- {pull}`277` ignores `DeprecationWarning` and `PendingDeprecationWarning` by default.
  Previously, they were enabled, but they should be shown when testing the project with
  pytest, not after the execution with pytask. Fixes {issue}`269`.
- {pull}`278` counts multiple occurrences of a warning instead of listing the module or
  task name again and again. Fixes {issue}`270`.

## 0.2.2 - 2022-05-14

- {pull}`267` fixes the info under the live execution table to show the total number of
  tasks also for pytask-parallel.
- {pull}`273` reworks `pytask clean` so that it ignores files tracked by git. Resolves
  {issue}`146`.

## 0.2.1 - 2022-04-28

- {pull}`259` adds an `.svg` for profiling tasks.
- {pull}`261` adds a config file option to sort entries in live table
- {pull}`262` allows pytask to capture warnings. Here is the
  [guide](https://pytask-dev.readthedocs.io/en/stable/how_to_guides/capture_warnings.html).

## 0.2.0 - 2022-04-14

- {pull}`211` allows for flexible dependencies and products which can be any pytree of
  native Python objects as supported by pybaum.
- {pull}`227` implements `task.kwargs` as a new way for a task to hold parametrized
  arguments. It also implements {class}`_pytask.models.CollectionMetadata` to carry
  parametrized arguments to the task class.
- {pull}`228` removes `task.pytaskmark` and moves the information to
  {attr}`_pytask.models.CollectionMetadata.markers`.
- {pull}`229` implements a new loop-based approach to parametrizations using the
  {func}`@pytask.mark.task <pytask.mark.task>` decorator.
- {pull}`230` implements {class}`_pytask.logging._TimeUnit` as a
  {class}`typing.NamedTuple` for better typing.
- {pull}`232` moves the documentation to MyST.
- {pull}`234` removes `MetaTask`. There is only {class}`pytask.Task`.
- {pull}`235` refactors the utility functions for dealing with marks in
  {mod}`_pytask.mark_utils`. (Closes {issue}`220`.)
- {pull}`236` refactors {mod}`_pytask.collect` and places shared functions in
  {mod}`_pytask.collect_utils`.
- {pull}`237` publish more functions.
- {pull}`238` allows any order of decorators with a `@pytask.mark.task` decorator.
- {pull}`239` adds a warning on globals for parametrizations and some fixes.
- {pull}`241` allows parametrizing over single dicts.
- {pull}`242` removes tasks from global {obj}`_pytask.task_utils.COLLECTED_TASKS` to
  avoid re-collection when the programmatic interface is used.
- {pull}`243` converts choice options to use enums instead of simple strings.
- {pull}`245` adds choices on the command line to the help pages as metavars and show
  defaults.
- {pull}`246` formalizes choices for {class}`click.Choice` to {class}`enum.Enum`.
- {pull}`252` adds a counter at the bottom of the execution table to show how many tasks
  have been processed.
- {pull}`253` adds support for `pyproject.toml`.
- {pull}`254` improves test coverage, fixes a bug, and improves the deprecation message
  for the configuration.
- {pull}`255` converts the readme to markdown and multiple pngs to svgs.
- {pull}`256` adds even more svgs and scripts to generate them to the documentation and
  other improvements.

## 0.1.9 - 2022-02-23

- {pull}`197` publishes types, and adds classes and functions to the main namespace.
- {pull}`217` enhances the tutorial on how to set up a project.
- {pull}`218` removes `depends_on` and `produces` from the task function when parsed.
- {pull}`219` removes some leftovers from pytest in {class}`~_pytask.mark.Mark`.
- {pull}`221` adds more test cases for parametrizations.
- {pull}`222` adds an automated Github Actions job for creating a list pytask plugins.
- {pull}`225` fixes a circular import noticeable in plugins created by {pull}`197`.
- {pull}`226` fixes a bug where the number of items in the live table during the
  execution is not exhausted. (Closes {issue}`223`.)

## 0.1.8 - 2022-02-07

- {pull}`210` allows `__tracebackhide__` to be a callable that accepts the current
  exception as an input. Closes {issue}`145`.
- {pull}`213` improves coverage and reporting.
- {pull}`215` makes the help pages of the CLI prettier.

## 0.1.7 - 2022-01-28

- {pull}`153` adds support for Python 3.10 which requires pony >= 0.7.15.
- {pull}`192` deprecates Python 3.6.
- {pull}`209` cancels previous CI jobs when a new job is started.

## 0.1.6 - 2022-01-27

- {pull}`191` adds a guide on how to profile pytask to the developer's guide.
- {pull}`192` deprecates Python 3.6.
- {pull}`193` adds more figures to the documentation.
- {pull}`194` updates the `README.rst`.
- {pull}`196` references the two new cookiecutters for projects and plugins.
- {pull}`198` fixes the documentation of
  {func}`@pytask.mark.skipif <pytask.mark.skipif>`. (Closes {issue}`195`)
- {pull}`199` extends the error message when paths are ambiguous on case-insensitive
  file systems.
- {pull}`200` implements the {func}`@pytask.mark.task <pytask.mark.task>` decorator to
  mark functions as tasks regardless of whether they are prefixed with `task_` or not.
- {pull}`201` adds tests for `_pytask.mark_utils`.
- {pull}`204` removes internal traceback frames from exceptions raised somewhere in
  pytask.
- {pull}`208` fixes the best practices guide for parametrizations.
- {pull}`209` cancels previous CI runs automatically.
- {pull}`212` add `.coveragerc` and improve coverage.

## 0.1.5 - 2022-01-10

- {pull}`184` refactors {func}`~_pytask.shared.reduce_node_name` and shorten task names
  in many places.
- {pull}`185` fix issues with drawing a graph and adds the `--rank-direction` to change
  the direction of the DAG.
- {pull}`186` enhance live displays by deactivating auto-refresh, among other things.
- {pull}`187` allows to enable and disable showing tracebacks and potentially different
  styles in the future with {confval}`show_traceback=True|False`.
- {pull}`188` refactors some code related to {class}`_pytask.enums.ExitCode`.
- {pull}`189` do not display a table in the execution if no task was run.
- {pull}`190` updates the release notes.

## 0.1.4 - 2022-01-04

- {pull}`153` adds support and testing for Python 3.10.
- {pull}`159` removes files for creating a conda package which is handled by
  conda-forge.
- {pull}`160` adds rudimentary typing to pytask.
- {pull}`161` removes a workaround for pyreadline which is also removed in pytest 7.
- {pull}`163` allow forward slashes in expressions and marker expressions.
- {pull}`164` allows to use backward slashes in expressions and marker expressions.
- {pull}`167` makes small changes to the docs.
- {pull}`172` embeds URLs in task ids. See {confval}`editor_url_scheme` for more
  information.
- {pull}`173` replaces `ColorCode` with custom rich themes.
- {pull}`174` restructures loosely defined outcomes to clear `enum.Enum`.
- {pull}`176` and {pull}`177` implement a summary panel that holds aggregate information
  about the number of successes, fails and other status.
- {pull}`178` adds stylistic changes like reducing tasks ids even more and dimming the
  path part.
- {pull}`180` fixes parsing relative paths from the configuration file.
- {pull}`181` adds correct formatting of running tasks.
- {pull}`182` introduces that only the starting year is displayed in the license
  following <https://hynek.me/til/copyright-years>.
- {pull}`183` enables tracing down the source of a function through decorators.

## 0.1.3 - 2021-11-30

- {pull}`157` adds packaging to the dependencies of the package.
- {pull}`158` converts time units to the nearest integer.

## 0.1.2 - 2021-11-27

- {pull}`135` implements handling of version in docs as proposed by setuptools-scm.
- {pull}`142` removes the display of skipped and persisted tasks from the live execution
  table for the default verbosity level of 1. They are displayed at 2.
- {pull}`144` adds tryceratops to the pre-commit hooks for catching issues with
  exceptions.
- {pull}`151` adds a limit on the number of items displayed in the execution table which
  is configurable with {confval}`n_entries_in_table` in the configuration file.
- {pull}`152` makes the duration of the execution readable by humans by separating it
  into days, hours, minutes and seconds.
- {pull}`155` implements functions to check for optional packages and programs and
  raises errors for requirements to draw the DAG earlier.
- {pull}`156` adds the option {confval}`show_errors_immediately` to print/show errors as
  soon as they occur. Resolves {issue}`150`.

## 0.1.1 - 2021-08-25

- {pull}`138` changes the default {confval}`verbosity` to `1` which displays the live
  table during execution and `0` display the symbols for outcomes (e.g. `.`, `F`, `s`).
- {pull}`139` enables rich's auto-refresh mechanism for live objects which causes almost
  no performance penalty for the live table compared to the symbolic output.

## 0.1.0 - 2021-07-20

- {pull}`106` implements a verbose mode for the execution which is available with
  `pytask -v` and shows a table with running and completed tasks. It also refines the
  collection status.
- {pull}`116`, {pull}`117`, and {pull}`123` fix {issue}`104` which prevented to skip
  tasks with missing dependencies.
- {pull}`118` makes the path to the configuration in the session header os-specific.
- {pull}`119` changes that when marker or keyword expressions are used to select tasks,
  also the predecessors of the selected tasks will be executed.
- {pull}`120` implements that a single `KeyboardInterrupt` stops the execution and
  previously collected reports are shown. Fixes {issue}`111`.
- {pull}`121` add skipped and persisted tasks to the execution footer.
- {pull}`127` make the table during execution the default. Silence pytask with negative
  verbose mode integers and increase verbosity with positive ones.
- {pull}`129` allows to hide frames from the traceback by using
  `__tracebackhide__ = True`.
- {pull}`130` enables rendering of tracebacks from subprocesses with rich.

## 0.0.16 - 2021-06-25

- {pull}`113` fixes error when using `pytask --version` with click v8.

## 0.0.15 - 2021-06-24

- {pull}`80` replaces some remaining formatting using `pprint` with `rich`.
- {pull}`81` adds a warning if a path is not correctly cased on a case-insensitive file
  system. This facilitates cross-platform builds of projects. Deactivate the check by
  setting `check_casing_of_paths = false` in the configuration file. See
  {confval}`check_casing_of_paths` for more information.
- {pull}`83` replaces `versioneer` with `setuptools_scm`.
- {pull}`84` fixes an error in the path normalization introduced by {pull}`81`.
- {pull}`85` sorts collected tasks, dependencies, and products by name.
- {pull}`87` fixes that dirty versions are displayed in the documentation.
- {pull}`88` adds the `pytask profile` command to show information on tasks like
  duration and file size of products.
- {pull}`93` fixes the display of parametrized arguments in the console.
- {pull}`94` adds {confval}`show_locals` which allows to print local variables in
  tracebacks.
- {pull}`96` implements a spinner to show the progress during the collection.
- {pull}`99` enables color support in WSL and fixes {confval}`show_locals` during
  collection.
- {pull}`101` implement to visualize the project's DAG. {pull}`108` refines the
  implementation.
- {pull}`102` adds an example if a parametrization provides not the number of arguments
  specified in the signature.
- {pull}`105` simplifies the logging of the tasks.
- {pull}`107` adds and new hook {func}`~_pytask.hookspecs.pytask_unconfigure` which
  makes pytask return {func}`pdb.set_trace` at the end of a session which allows to use
  {func}`breakpoint` inside test functions using pytask.
- {pull}`109` makes pytask require networkx>=2.4 since previous versions fail with
  Python 3.9.
- {pull}`110` adds a "New Features" section to the `README.rst`.

## 0.0.14 - 2021-03-23

- {pull}`74` reworks the formatting of the command line output by using `rich`. Due to
  the new dependency, support for pytask with Python \<3.6.1 on PyPI and with Python
  \<3.7 on Anaconda will end.
- {pull}`76` fixes {issue}`75` which reports a bug when a closest ancestor cannot be
  found to shorten node names in the CLI output. Instead a common ancestor is used.

## 0.0.13 - 2021-03-09

- {pull}`72` adds conda-forge to the README and highlights importance of specifying
  dependencies and products.
- {pull}`62` implements the {func}`pytask.mark.skipif` marker to conditionally skip
  tasks. Many thanks to {user}`roecla` for implementing this feature and a warm welcome
  since she is the first pytask contributor!

## 0.0.12 - 2021-02-27

- {pull}`55` implements miscellaneous fixes to improve error message, tests and
  coverage.
- {pull}`59` adds a tutorial on using plugins and features plugins more prominently.
- {pull}`60` adds the MIT license to the project and mentions pytest and its developers.
- {pull}`61` adds many changes to the documentation.
- {pull}`65` adds versioneer to pytask and {pull}`66` corrects the coverage reports
  which were deflated due to the new files.
- {pull}`67` prepares pytask to be published on PyPI and {pull}`68` fixes the pipeline,
  and {pull}`69` prepares releasing v0.0.12 and adds new shields.

## 0.0.11 - 2020-12-27

- {pull}`45` adds the option to stop execution after a number of tasks has failed.
  Closes {issue}`44`.
- {pull}`47` reduce node names in error messages while resolving dependencies.
- {pull}`49` starts a style guide for pytask.
- {pull}`50` implements correct usage of singular and plural in collection logs.
- {pull}`51` allows to invoke pytask through the Python interpreter with
  `python -m pytask` which will add the current path to `sys.path`.
- {pull}`52` allows to prioritize tasks with `pytask.mark.try_last` and
  `pytask.mark.try_first`.
- {pull}`53` changes the theme of the documentation to furo.
- {pull}`54` releases v0.0.11.

## 0.0.10 - 2020-11-18

- {pull}`40` cleans up the capture manager and other parts of pytask.
- {pull}`41` shortens the task ids in the error reports for better readability.
- {pull}`42` ensures that lists with one element and dictionaries with only a zero key
  as input for `@pytask.mark.depends_on` and `@pytask.mark.produces` are preserved as a
  dictionary inside the function.

## 0.0.9 - 2020-10-28

- {pull}`31` adds `pytask collect` to show information on collected tasks.
- {pull}`32` fixes `pytask clean`.
- {pull}`33` adds a module to apply common parameters to the command line interface.
- {pull}`34` skips `pytask_collect_task_teardown` if task is None.
- {pull}`35` adds the ability to capture stdout and stderr with the CaptureManager.
- {pull}`36` reworks the debugger to make it work with the CaptureManager.
- {pull}`37` removes `reports` argument from hooks related to task collection.
- {pull}`38` allows to pass dictionaries as dependencies and products and inside the
  function `depends_on` and `produces` become dictionaries.
- {pull}`39` releases v0.0.9.

## 0.0.8 - 2020-10-04

- {pull}`30` fixes or adds the session object to some hooks which was missing from the
  previous release.

## 0.0.7 - 2020-10-03

- {pull}`25` allows to customize the names of the task files.
- {pull}`26` makes commands return the correct exit codes.
- {pull}`27` implements the `pytask_collect_task_teardown` hook specification to perform
  checks after a task is collected.
- {pull}`28` implements the `@pytask.mark.persist` decorator.
- {pull}`29` releases 0.0.7.

## 0.0.6 - 2020-09-12

- {pull}`16` reduces the traceback generated from tasks, failure section in report, fix
  error passing a file path to pytask, add demo to README.
- {pull}`17` changes the interface to subcommands, adds `"-c/--config"` option to pass a
  path to a configuration file and adds `pytask clean` ({pull}`22` as well), a command
  to clean your project.
- {pull}`18` changes the documentation theme to alabaster.
- {pull}`19` adds some changes related to ignored folders.
- {pull}`20` fixes copying code examples in the documentation.
- {pull}`21` enhances the ids generated by parametrization, allows to change them via
  the `ids` argument, and adds tutorials.
- {pull}`23` allows to specify paths via the configuration file, documents the cli and
  configuration options.
- {pull}`24` releases 0.0.6.

## 0.0.5 - 2020-08-12

- {pull}`10` turns parametrization into a plugin.
- {pull}`11` extends the documentation.
- {pull}`12` replaces `pytest.mark` with `pytask.mark`.
- {pull}`13` implements selecting tasks via expressions or marker expressions.
- {pull}`14` separates the namespace of pytask to `pytask` and `_pytask`.
- {pull}`15` implements better tasks ids which consists of
  \<path-to-task-file>::\<func-name> and are certainly unique. And, it releases 0.0.5.

## 0.0.4 - 2020-07-22

- {pull}`9` adds hook specifications to the parametrization of tasks which allows
  `pytask-latex` and `pytask-r` to pass different command line arguments to a
  parametrized task and its script. Also, it prepares the release of 0.0.4.

## 0.0.3 - 2020-07-19

- {pull}`7` makes pytask exit with code 1 if a task failed and the
  `skip_ancestor_failed` decorator is only applied to descendant tasks not the task
  itself.
- {pull}`8` releases v0.0.3

## 0.0.2 - 2020-07-17

- {pull}`2` provided multiple small changes.
- {pull}`3` implements a class which holds the execution report of one task.
- {pull}`4` makes adjustments after moving to `main` as the default branch.
- {pull}`5` adds `pytask_add_hooks` to add more hook specifications and register hooks.
- {pull}`6` releases v0.0.2.

## 0.0.1 - 2020-06-29

- {pull}`1` combined the whole effort which went into releasing v0.0.1.
