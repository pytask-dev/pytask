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
  [Stata](https://github.com/pytask-dev/pytask-stata), and more can be found
  [here](https://github.com/topics/pytask). Learn more about plugins in
  [this tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/plugins.html).

To get started with pytask, the documentation includes a series of tutorials. Go to the
first {doc}`tutorial <tutorials/installation>` for the installation and proceed from
there.

## Documentation

If you want to know more about pytask, dive into one of the following topics

`````{grid} 1 2 2 2
---
gutter: 3
---
````{grid-item-card}
:text-align: center
:img-top: _static/images/light-bulb.svg
:class-img-top: index-card-image
:class-item: only-light
:shadow: md

```{button-link} tutorials/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Tutorials
```

Tutorials help you to get started with pytask and how you manage your first project.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/light-bulb-light.svg
:class-img-top: index-card-image
:class-item: only-dark
:shadow: md

```{button-link} tutorials/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Tutorials
```

Tutorials help you to get started with pytask and how you manage your first project.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/book.svg
:class-img-top: index-card-image
:class-item: only-light
:shadow: md

```{button-link} how_to_guides/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
How-to Guides
```

How-to guides provide instructions for very specific and advanced tasks and document
best-practices.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/book-light.svg
:class-img-top: index-card-image
:class-item: only-dark
:shadow: md

```{button-link} how_to_guides/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
How-to Guides
```

How-to guides provide instructions for very specific and advanced tasks and document
best-practices.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/books.svg
:class-img-top: index-card-image
:class-item: only-light
:shadow: md

```{button-link} explanations/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Explanations
```

Explanations deal with key topics and concepts which underlie the package.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/books-light.svg
:class-img-top: index-card-image
:class-item: only-dark
:shadow: md

```{button-link} explanations/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Explanations
```

Explanations deal with key topics and concepts which underlie the package.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/coding.svg
:class-img-top: index-card-image
:class-item: only-light
:shadow: md

```{button-link} reference_guides/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Reference Guides
```

Reference guides explain the implementation and provide an entry-point for developers.

````

````{grid-item-card}
:text-align: center
:img-top: _static/images/coding-light.svg
:class-img-top: index-card-image
:class-item: only-dark
:shadow: md

```{button-link} reference_guides/index.html
---
click-parent:
ref-type: ref
class: stretched-link index-card-link
---
Reference Guides
```

Reference guides explain the implementation and provide an entry-point for developers.

````

`````

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
type_hints
developers_guide
glossary
changes
On Github <https://github.com/pytask-dev/pytask>
```
