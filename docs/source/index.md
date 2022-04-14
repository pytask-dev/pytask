# pytask

<!-- Keep in sync with README.md -->

[![PyPI](https://img.shields.io/pypi/v/pytask?color=blue)](https://pypi.org/project/pytask)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytask)](https://pypi.org/project/pytask)
[![image](https://img.shields.io/conda/vn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![image](https://img.shields.io/conda/pn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![PyPI - License](https://img.shields.io/pypi/l/pytask)](https://pypi.org/project/pytask)
[![image](https://readthedocs.org/projects/pytask-dev/badge/?version=latest)](https://pytask-dev.readthedocs.io/en/stable)
[![image](https://img.shields.io/github/workflow/status/pytask-dev/pytask/main/main)](https://github.com/pytask-dev/pytask/actions?query=branch%3Amain)
[![image](https://codecov.io/gh/pytask-dev/pytask/branch/main/graph/badge.svg)](https://app.codecov.io/gh/pytask-dev/pytask)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pytask-dev/pytask/main.svg)](https://results.pre-commit.ci/latest/github/pytask-dev/pytask/main)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

<!-- Keep in sync with README.md -->

pytask is a workflow management system which facilitates reproducible data analyses. Its
features include:

- **Automatic discovery of tasks.**
- **Lazy evaluation.** If a task, its dependencies, and its products have not changed,
  do not execute it.
- **Debug mode.**
  [Jump into the debugger](https://pytask-dev.readthedocs.io/en/stable/tutorials/debugging.html)
  if a task fails, get feedback quickly, and be more productive.
- **Repeat a task with different inputs.**
  [Loop over task functions](https://pytask-dev.readthedocs.io/en/stable/tutorials/repeating_tasks_with_different_inputs.html)
  to run the same task with different inputs.
- **Select tasks via expressions.** Run only a subset of tasks with
  [expressions and marker expressions](https://pytask-dev.readthedocs.io/en/stable/tutorials/selecting_tasks.html).
- **Easily extensible with plugins**. pytask is built on top of
  [pluggy](https://pluggy.readthedocs.io/en/latest/), a plugin management framework,
  which allows you to adjust pytask to your needs. Plugins are available for
  [parallelization](https://github.com/pytask-dev/pytask-parallel),
  [LaTeX](https://github.com/pytask-dev/pytask-latex),
  [R](https://github.com/pytask-dev/pytask-r), and
  [Stata](https://github.com/pytask-dev/pytask-stata) and more can be found
  [here](https://github.com/topics/pytask). Learn more about plungins in
  [this tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/plugins.html).

To get started with pytask, the documentation includes a series of tutorials. Go to the
first {doc}`tutorial <tutorials/installation>` for the installation and proceed from
there.

## Documentation

If you want to know more about pytask, dive into one the following topics.

```{eval-rst}
.. panels::
    :container: container pb-4
    :column: col-lg-6 col-md-6 col-sm-6 col-xs-12 p-2
    :card: shadow pt-4
    :body: text-center

    ---
    :img-top: _static/images/light-bulb.svg

    .. link-button:: tutorials/index
        :type: ref
        :text: Tutorials
        :classes: stretched-link font-weight-bold

    Tutorials help you to get started with pytask and how you manage your first project.

    ---
    :img-top: _static/images/book.svg

    .. link-button:: how_to_guides/index
        :type: ref
        :text: How-to Guides
        :classes: stretched-link font-weight-bold

    How-to guides provide instructions for very specific and advanced tasks and document
    best-practices.

    ---
    :img-top: _static/images/books.svg

    .. link-button:: explanations/index
        :type: ref
        :text: Explanations
        :classes: stretched-link font-weight-bold

    Explanations deal with key topics and concepts which underlie the package.

    ---
    :img-top: _static/images/coding.svg

    .. link-button:: reference_guides/index
        :type: ref
        :text: Reference Guides
        :classes: stretched-link font-weight-bold

    Reference guides explain the implementation and provide an entry-point for
    developers.

```

```{toctree}
---
hidden: true
---
tutorials/index
how_to_guides/index
explanations/index
reference_guides/index
```

Furthermore, the documentation includes the following topics.

```{toctree}
---
maxdepth: 1
---
plugin_list
api
developers_guide
glossary
changes
On Github <https://github.com/pytask-dev/pytask>
```
