Release notes
=============

This is a record of all past ``pipeline`` releases and what went into them in reverse
chronological order. We follow `semantic versioning <https://semver.org/>`_ and all
releases are available on `Anaconda.org
<https://anaconda.org/opensourceeconomics/pipeline>`_.


0.0.6 - 2020-
-------------

- Add ``run_always`` to the task dictionary to always execute a task (:gh:`12`).
- Add project root directory to the ``PYTHONPATH`` so that every task can import with
  ``from src.... import ...`` (:gh:`13`).
- Split coverage reports into unit, integration, and end-to-end tests (:gh:`14`).
- Allow to have directories as task dependencies and targets (:gh:`15`).
- Handle multiple targets of tasks (:gh:`18`).
- Fix exception handling in the parallel executor (:gh:`19`).


0.0.5 - 2020-04-26
------------------

- Added ``pydot`` as a package dependency  and added all information in ``config`` to
  render a task template (:gh:`11`).
- Remove references to respy (:gh:`8`).
- Fix codecov (:gh:`7`).


0.0.4 - 2020-04-06
------------------

- Added task scheduling with priorities for serial and parallel workflows (:gh:`4`).
- More documentation (:gh:`4`).
- Changes in rendered task templates cause a task to re-run (:gh:`4`).


0.0.3 - 2020-03-31
------------------

- Additional templates for plotting (:gh:`5`).
- Templates for the estimation of ordinal models (:gh:`3`).
- Automatic variable label conversion to LaTeX conform labels for r-stargazer (:gh:`5`).


0.0.2 - 2020-03-29
------------------

- Parallel execution of tasks (:gh:`2`).


0.0.1 - 2020-03-26
------------------

- Initial release.
