# pytask

<!-- Keep in sync with README.md -->

[![PyPI](https://img.shields.io/pypi/v/pytask?color=blue)](https://pypi.org/project/pytask)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytask)](https://pypi.org/project/pytask)
[![image](https://img.shields.io/conda/vn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![image](https://img.shields.io/conda/pn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![PyPI - License](https://img.shields.io/pypi/l/pytask)](https://pypi.org/project/pytask)
[![image](https://readthedocs.org/projects/pytask-dev/badge/?version=latest)](https://pytask-dev.readthedocs.io/en/stable)
[![image](https://img.shields.io/github/actions/workflow/status/pytask-dev/pytask/main.yml?branch=main)](https://github.com/pytask-dev/pytask/actions?query=branch%3Amain)
[![image](https://codecov.io/gh/pytask-dev/pytask/branch/main/graph/badge.svg)](https://app.codecov.io/gh/pytask-dev/pytask)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pytask-dev/pytask/main.svg)](https://results.pre-commit.ci/latest/github/pytask-dev/pytask/main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Features

<!-- Keep in sync with README.md -->

pytask is a [workflow management system](glossary.md#workflow-management-system) that
facilitates reproducible data analyses. Its features include:

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
    [Stata](https://github.com/pytask-dev/pytask-stata), and more can be found
    [here](https://github.com/topics/pytask). Learn more about plugins in
    [this tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/plugins.html).

To get started with pytask, the documentation includes a series of tutorials. Go to the
first [tutorial](tutorials/installation.md) for the installation and proceed from there.

## Documentation

If you want to know more about pytask, dive into one of the following topics.

<div class="home-tiles">
  <a class="home-tile" href="tutorials/index.html">
    <img src="_static/images/light-bulb.svg" alt="Tutorials icon">
    <h3>Tutorials</h3>
    <p>Tutorials help you get started with pytask and build your first project.</p>
  </a>
  <a class="home-tile" href="how_to_guides/index.html">
    <img src="_static/images/book.svg" alt="How-to guides icon">
    <h3>How-to Guides</h3>
    <p>Step-by-step instructions for concrete tasks and advanced workflows.</p>
  </a>
  <a class="home-tile" href="explanations/index.html">
    <img src="_static/images/books.svg" alt="Explanations icon">
    <h3>Explanations</h3>
    <p>Background and conceptual context for design decisions in pytask.</p>
  </a>
  <a class="home-tile" href="reference_guides/index.html">
    <img src="_static/images/coding.svg" alt="Reference guides icon">
    <h3>Reference Guides</h3>
    <p>API and implementation details for developers and plugin authors.</p>
  </a>
</div>

For command-line usage, see the [CLI reference](commands/index.md).
