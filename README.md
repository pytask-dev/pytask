<a href="https://pytask-dev.readthedocs.io/en/stable">
    <p align="center">
        <img src="https://raw.githubusercontent.com/pytask-dev/pytask/main/docs/source/_static/images/pytask_w_text.png" width=50% alt="pytask">
    </p>
</a>

______________________________________________________________________

<!-- Keep in sync with docs/source/index.md -->

[![PyPI](https://img.shields.io/pypi/v/pytask?color=blue)](https://pypi.org/project/pytask)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytask)](https://pypi.org/project/pytask)
[![image](https://img.shields.io/conda/vn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![image](https://img.shields.io/conda/pn/conda-forge/pytask.svg)](https://anaconda.org/conda-forge/pytask)
[![PyPI - License](https://img.shields.io/pypi/l/pytask)](https://pypi.org/project/pytask)
[![image](https://readthedocs.org/projects/pytask-dev/badge/?version=latest)](https://pytask-dev.readthedocs.io/en/stable)
[![image](https://img.shields.io/github/actions/workflow/status/pytask-dev/pytask/main.yml?branch=main)](https://github.com/pytask-dev/pytask/actions?query=branch%3Amain)
[![image](https://codecov.io/gh/pytask-dev/pytask/branch/main/graph/badge.svg)](https://app.codecov.io/gh/pytask-dev/pytask)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pytask-dev/pytask/main.svg)](https://results.pre-commit.ci/latest/github/pytask-dev/pytask/main)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- Keep in sync with docs/source/index.md -->

pytask is a workflow management system that facilitates reproducible data analyses. Its
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
  [here](https://github.com/topics/pytask). Learn more about plugins in
  [this tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/plugins.html).

# Installation

<!-- Keep in sync with docs/source/tutorials/installation.md -->

pytask is available on [PyPI](https://pypi.org/project/pytask) and on
[Anaconda.org](https://anaconda.org/conda-forge/pytask). Install the package with

```console
$ pip install pytask
```

or

```console
$ conda install -c conda-forge pytask
```

Color support is automatically available on non-Windows platforms. On Windows, please,
use [Windows Terminal](https://github.com/microsoft/terminal), which can be, for
example, installed via the [Microsoft Store](https://aka.ms/terminal).

To quickly set up a new project, use the
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project)
template or start from
[other templates or example projects](https://pytask-dev.readthedocs.io/en/stable/how_to_guides/bp_templates_and_projects.html).

# Usage

A task is a function that is detected if the module and the function name are prefixed
with `task_`. Here is an example.

```python
# Content of task_hello.py.

import pytask


@pytask.mark.produces("hello_earth.txt")
def task_hello_earth(produces):
    produces.write_text("Hello, earth!")
```

Here are some details:

- Dependencies and products of a task are tracked via markers. Use
  `@pytask.mark.depends_on` for dependencies and `@pytask.mark.produces` for products.
  Values are strings or `pathlib.Path` and point to files on the disk.
- Use `produces` (and `depends_on`) as function arguments to access the paths inside the
  function. pytask converts all paths to `pathlib.Path`'s. Here, `produces` holds the
  path to `"hello_earth.txt"`.

To execute the task, enter `pytask` on the command-line

![image](https://github.com/pytask-dev/pytask/raw/main/docs/source/_static/images/readme.gif)

# Documentation

You find the documentation <https://pytask-dev.readthedocs.io/en/stable> with
[tutorials](https://pytask-dev.readthedocs.io/en/stable/tutorials/index.html) and guides
for
[best practices](https://pytask-dev.readthedocs.io/en/stable/how_to_guides/index.html).

# Changes

Consult the [release notes](https://pytask-dev.readthedocs.io/en/stable/changes.html) to
find out about what is new.

# License

pytask is distributed under the terms of the [MIT license](LICENSE).

# Acknowledgment

The license also includes a copyright and permission notice from
[pytest](https://github.com/pytest-dev/pytest) since some modules, classes, and
functions are copied from pytest. Not to mention how pytest has inspired the development
of pytask in general. Without the excellent work of
[Holger Krekel](https://github.com/hpk42) and pytest's many contributors, this project
would not have been possible. Thank you!

pytask owes its beautiful appearance on the command line to
[rich](https://github.com/Textualize/rich), written by
[Will McGugan](https://github.com/willmcgugan).

Repeating tasks in loops is inspired by [ward](https://github.com/darrenburns/ward)
written by [Darren Burns](https://github.com/darrenburns).

# Citation

If you rely on pytask to manage your research project, please cite it with the following
key to help others to discover the tool.

```bibtex
@Unpublished{Raabe2020,
    Title  = {A Python tool for managing scientific workflows.},
    Author = {Tobias Raabe},
    Year   = {2020},
    Url    = {https://github.com/pytask-dev/pytask}
}
```
