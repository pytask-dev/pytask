Changes
=======

This is a record of all past pytask releases and what went into them in reverse
chronological order. Releases follow `semantic versioning <https://semver.org/>`_ and
all releases are available on `PyPI <https://pypi.org/project/pytask>`_ and
`Anaconda.org <https://anaconda.org/conda-forge/pytask>`_.


0.1.4 - 2021-xx-xx
------------------

- :gh:`159` removes files for creating a conda package which is handled by conda-forge.
- :gh:`160` adds typing to pytask.
- :gh:`161` removes a workaround for pyreadline which is also removed in pytest 7.
- :gh:`163` allow forward slashes in expressions and marker expressions.
- :gh:`164` allows to use backward slashes in expressions and marker expressions.


0.1.3 - 2021-11-30
------------------

- :gh:`157` adds packaging to the dependencies of the package.
- :gh:`158` converts time units to the nearest integer.


0.1.2 - 2021-11-27
------------------

- :gh:`135` implements handling of version in docs as proposed by setuptools-scm.
- :gh:`142` removes the display of skipped and persisted tasks from the live execution
  table for the default verbosity level of 1. They are displayed at 2.
- :gh:`144` adds tryceratops to the pre-commit hooks for catching issues with
  exceptions.
- :gh:`150` adds a limit on the number of items displayed in the execution table which
  is also configurable with ``--n-entries-in-table`` on the cli and
  ``n_entries_in_table`` in the configuration file.
- :gh:`152` makes the duration of the execution readable by humans by separating it into
  days, hours, minutes and seconds.
- :gh:`155` implements functions to check for optional packages and programs and raises
  errors for requirements to draw the DAG earlier.
- :gh:`156` adds an option to print/show errors as soon as they occur.


0.1.1 - 2021-08-25
------------------

- :gh:`138` changes the default verbosity to ``1`` which displays the live table during
  execution and ``0`` display the symbols for outcomes (e.g. ``.``, ``F``, ``s``).
- :gh:`139` enables rich's auto-refresh mechanism for live objects which causes almost
  no performance penalty for the live table compared to the symbolic output.


0.1.0 - 2021-07-20
------------------

- :gh:`106` implements a verbose mode for the execution which is available with ``pytask
  -v`` and shows a table with running and completed tasks. It also refines the
  collection status.
- :gh:`116`, :gh:`117`, and :gh:`123` fix :gh:`104` which prevented to skip tasks with
  missing dependencies.
- :gh:`118` makes the path to the configuration in the session header os-specific.
- :gh:`119` changes that when marker or keyword expressions are used to select tasks,
  also the predecessors of the selected tasks will be executed.
- :gh:`120` implements that a single ``KeyboardInterrupt`` stops the execution and
  previously collected reports are shown.
- :gh:`121` add skipped and persisted tasks to the execution footer.
- :gh:`127` make the table during execution the default. Silence pytask with negative
  verbose mode integers and increase verbosity with positive ones.
- :gh:`129` allows to hide frames from the traceback by using ``__tracebackhide__ =
  True``.
- :gh:`130` enables rendering of tracebacks from subprocesses with rich.


0.0.16 - 2021-06-25
-------------------

- :gh:`111` fixes error when using ``pytask --version`` with click v8.


0.0.15 - 2021-06-24
-------------------

- :gh:`80` replaces some remaining formatting using ``pprint`` with ``rich``.
- :gh:`81` adds a warning if a path is not correctly cased on a case-insensitive file
  system. This facilitates cross-platform builds of projects. Deactivate the check by
  setting ``check_casing_of_paths = false`` in the configuration file.
- :gh:`83` replaces ``versioneer`` with ``setuptools_scm``.
- :gh:`84` fixes an error in the path normalization introduced by :gh:`81`.
- :gh:`85` sorts collected tasks, dependencies, and products by name.
- :gh:`87` fixes that dirty versions are displayed in the documentation.
- :gh:`88` adds a ``profile`` command to show information on tasks like duration and
  file size of products.
- :gh:`93` fixes the display of parametrized arguments in the console.
- :gh:`94` adds ``--show-locals`` which allows to print local variables in tracebacks.
- :gh:`96` implements a spinner to show the progress during the collection.
- :gh:`99` enables color support in WSL and fixes ``show_locals`` during collection.
- :gh:`101` implement to visualize the project's DAG. :gh:`108` refines the
  implementation.
- :gh:`102` adds an example if a parametrization provides not the number of arguments
  specified in the signature.
- :gh:`105` simplifies the logging of the tasks.
- :gh:`107` adds and new hook ``pytask_unconfigure`` which makes pytask return
  :func:`pdb.set_trace` at the end of a session which allows to use ``breakpoint()``
  inside test functions using pytask.
- :gh:`109` makes pytask require networkx>=2.4 since previous versions fail with Python
  3.9.
- :gh:`110` adds a "New Features" section to the ``README.rst``.


0.0.14 - 2021-03-23
-------------------

- :gh:`74` reworks the formatting of the command line output by using ``rich``. Due to
  the new dependency, support for pytask with Python <3.6.1 on PyPI and with Python <3.7
  on Anaconda will end.
- :gh:`76` fixes :gh:`75` which reports a bug when a closest ancestor cannot be found to
  shorten node names in the CLI output. Instead a common ancestor is used.


0.0.13 - 2021-03-09
-------------------

- :gh:`72` adds conda-forge to the README and highlights importance of specifying
  dependencies and products.
- :gh:`62` implements the ``pytask.mark.skipif`` marker to conditionally skip tasks.
  Many thanks to :ghuser:`roecla` for implementing this feature and a warm welcome since
  she is the first pytask contributor!


0.0.12 - 2021-02-27
-------------------

- :gh:`55` implements miscellaneous fixes to improve error message, tests and coverage.
- :gh:`59` adds a tutorial on using plugins and features plugins more prominently.
- :gh:`60` adds the MIT license to the project and mentions pytest and its developers.
- :gh:`61` adds many changes to the documentation.
- :gh:`65` adds versioneer to pytask and :gh:`66` corrects the coverage reports which
  were deflated due to the new files.
- :gh:`67` prepares pytask to be published on PyPI and :gh:`68` fixes the pipeline, and
  :gh:`69` prepares releasing v0.0.12 and adds new shields.


0.0.11 - 2020-12-27
-------------------

- :gh:`45` adds the option to stop execution after a number of tasks has failed. Closes
  :gh:`44`.
- :gh:`47` reduce node names in error messages while resolving dependencies.
- :gh:`49` starts a style guide for pytask.
- :gh:`50` implements correct usage of singular and plural in collection logs.
- :gh:`51` allows to invoke pytask through the Python interpreter with ``python -m
  pytask`` which will add the current path to ``sys.path``.
- :gh:`52` allows to prioritize tasks with ``pytask.mark.try_last`` and
  ``pytask.mark.try_first``.
- :gh:`53` changes the theme of the documentation to furo.
- :gh:`54` releases v0.0.11.


0.0.10 - 2020-11-18
-------------------

- :gh:`40` cleans up the capture manager and other parts of pytask.
- :gh:`41` shortens the task ids in the error reports for better readability.
- :gh:`42` ensures that lists with one element and dictionaries with only a zero key as
  input for ``@pytask.mark.depends_on`` and ``@pytask.mark.produces`` are preserved as a
  dictionary inside the function.


0.0.9 - 2020-10-28
------------------

- :gh:`31` adds ``pytask collect`` to show information on collected tasks.
- :gh:`32` fixes ``pytask clean``.
- :gh:`33` adds a module to apply common parameters to the command line interface.
- :gh:`34` skips ``pytask_collect_task_teardown`` if task is None.
- :gh:`35` adds the ability to capture stdout and stderr with the CaptureManager.
- :gh:`36` reworks the debugger to make it work with the CaptureManager.
- :gh:`37` removes ``reports`` argument from hooks related to task collection.
- :gh:`38` allows to pass dictionaries as dependencies and products and inside the
  function ``depends_on`` and ``produces`` become dictionaries.
- :gh:`39` releases v0.0.9.


0.0.8 - 2020-10-04
------------------

- :gh:`30` fixes or adds the session object to some hooks which was missing from the
  previous release.


0.0.7 - 2020-10-03
------------------

- :gh:`25` allows to customize the names of the task files.
- :gh:`26` makes commands return the correct exit codes.
- :gh:`27` implements the ``pytask_collect_task_teardown`` hook specification to perform
  checks after a task is collected.
- :gh:`28` implements the ``@pytask.mark.persist`` decorator.
- :gh:`29` releases 0.0.7.


0.0.6 - 2020-09-12
------------------

- :gh:`16` reduces the traceback generated from tasks, failure section in report, fix
  error passing a file path to pytask, add demo to README.
- :gh:`17` changes the interface to subcommands, adds ``"-c/--config"`` option to pass a
  path to a configuration file and adds ``pytask clean`` (:gh:`22` as well), a command
  to clean your project.
- :gh:`18` changes the documentation theme to alabaster.
- :gh:`19` adds some changes related to ignored folders.
- :gh:`20` fixes copying code examples in the documentation.
- :gh:`21` enhances the ids generated by parametrization, allows to change them via the
  ``ids`` argument, and adds tutorials.
- :gh:`23` allows to specify paths via the configuration file, documents the cli and
  configuration options.
- :gh:`24` releases 0.0.6.


0.0.5 - 2020-08-12
------------------

- :gh:`10` turns parametrization into a plugin.
- :gh:`11` extends the documentation.
- :gh:`12` replaces ``pytest.mark`` with ``pytask.mark``.
- :gh:`13` implements selecting tasks via expressions or marker expressions.
- :gh:`14` separates the namespace of pytask to ``pytask`` and ``_pytask``.
- :gh:`15` implements better tasks ids which consists of
  <path-to-task-file>::<func-name> and are certainly unique. And, it releases 0.0.5.


0.0.4 - 2020-07-22
------------------

- :gh:`9` adds hook specifications to the parametrization of tasks which allows
  ``pytask-latex`` and ``pytask-r`` to pass different command line arguments to a
  parametrized task and its script. Also, it prepares the release of 0.0.4.


0.0.3 - 2020-07-19
------------------

- :gh:`7` makes pytask exit with code 1 if a task failed and the
  ``skip_ancestor_failed`` decorator is only applied to descendant tasks not the task
  itself.
- :gh:`8` releases v0.0.3


0.0.2 - 2020-07-17
------------------

- :gh:`2` provided multiple small changes.
- :gh:`3` implements a class which holds the execution report of one task.
- :gh:`4` makes adjustments after moving to ``main`` as the default branch.
- :gh:`5` adds ``pytask_add_hooks`` to add more hook specifications and register hooks.
- :gh:`6` releases v0.0.2.


0.0.1 - 2020-06-29
------------------

- :gh:`1` combined the whole effort which went into releasing v0.0.1.
