# Changes

This is a record of all past pytask releases and what went into them in reverse
chronological order. Releases follow [semantic versioning](https://semver.org/) and all
releases are available on [PyPI](https://pypi.org/project/pytask) and
[Anaconda.org](https://anaconda.org/conda-forge/pytask).

## 0.2.0 - 2022-xx-xx

- {pull}`211` allows for flexible dependencies and products which can be any pytree of
  native Python objects as supported by pybaum.
- {pull}`227` implements `task.kwargs` as a new way for a task to hold parametrized
  arguments. It also implements {class}`_pytask.models.CollectionMetadata` to carry
  parametrized arguments to the task class.
- {pull}`228` removes `task.pytaskmark` and moves the information to
  {attr}`_pytask.models.CollectionMetadata.markers`.
- {pull}`229` implements a new loop-based approach to parametrizations using the
  {func}`@pytask.mark.task <_pytask.task.task>` decorator.

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

- {pull}`210` allows `__tracebackhide__` to be a callable which accepts the current
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
  {func}`@pytask.mark.skipif <_pytask.skipping.skipif>`. (Closes {issue}`195`)
- {pull}`199` extends the error message when paths are ambiguous on case-insensitive
  file systems.
- {pull}`200` implements the {func}`@pytask.mark.task <_pytask.task.task>` decorator to
  mark functions as tasks regardless whether they are prefixed with `task_` or not.
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
- {pull}`186` enhance live displays by deactivating auto-refresh among other things.
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
- {pull}`176` and {pull}`177` implement a summary panel which holds aggregate
  information about the number of successes, fails and other status.
- {pull}`178` makes some stylistic changes like reducing tasks ids even more and dims
  the path part.
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
- {pull}`150` adds a limit on the number of items displayed in the execution table which
  is configurable with {confval}`n_entries_in_table` in the configuration file.
- {pull}`152` makes the duration of the execution readable by humans by separating it
  into days, hours, minutes and seconds.
- {pull}`155` implements functions to check for optional packages and programs and
  raises errors for requirements to draw the DAG earlier.
- {pull}`156` adds the option {confval}`show_errors_immediately` to print/show errors as
  soon as they occur.

## 0.1.1 - 2021-08-25

- {pull}`138` changes the default {confval}`verbosity` to `1` which displays the live
  table during execution and `0` display the symbols for outcomes (e.g. `.`, `F`, `s`).
- {pull}`139` enables rich's auto-refresh mechanism for live objects which causes almost
  no performance penalty for the live table compared to the symbolic output.

## 0.1.0 - 2021-07-20

- {pull}`106` implements a verbose mode for the execution which is available with
  `pytask -v` and shows a table with running and completed tasks. It also refines the
  collection status.
- {pull}`116`, {pull}`117`, and {pull}`123` fix {pull}`104` which prevented to skip
  tasks with missing dependencies.
- {pull}`118` makes the path to the configuration in the session header os-specific.
- {pull}`119` changes that when marker or keyword expressions are used to select tasks,
  also the predecessors of the selected tasks will be executed.
- {pull}`120` implements that a single `KeyboardInterrupt` stops the execution and
  previously collected reports are shown.
- {pull}`121` add skipped and persisted tasks to the execution footer.
- {pull}`127` make the table during execution the default. Silence pytask with negative
  verbose mode integers and increase verbosity with positive ones.
- {pull}`129` allows to hide frames from the traceback by using
  `__tracebackhide__ = True`.
- {pull}`130` enables rendering of tracebacks from subprocesses with rich.

## 0.0.16 - 2021-06-25

- {pull}`111` fixes error when using `pytask --version` with click v8.

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
- {pull}`76` fixes {pull}`75` which reports a bug when a closest ancestor cannot be
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
  Closes {pull}`44`.
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