# Set up a project

To use pytask for larger projects, organize the project as a Python package. This
tutorial explains the minimal setup.

If you want to use pytask with a collection of scripts, you can skip this lesson and
move to the next section of the tutorials.

!!! note

```
In case you are thinking about developing multiple packages in the project that should be separated (one for dealing with the data, one for the analysis and a package for the pytask tasks), consider using a [workspace](../how_to_guides/using_workspaces.md).
```

## The directory structure

The following directory tree gives an overview of the project's different parts.

```text
my_project
│
├───.pytask
│
├───bld
│   └────...
│
├───src
│   └───my_project
│       ├────__init__.py
│       ├────config.py
│       └────...
│
└───pyproject.toml
```

Replicate this directory structure for your project or start from pytask's
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project)
template or any other
[linked template or example project](../how_to_guides/bp_templates_and_projects.md).

## The `src` directory

The `src` directory only contains a folder for the project in which the tasks and source
files reside. The nested structure is called the "`src` layout" and is the preferred way
to structure Python packages.

It contains a `config.py` or a similar module to store the project's configuration. You
should define paths pointing to the source and build directory of the project. They
later help to define other paths.

```python
# Content of config.py.
from pathlib import Path


SRC = Path(__file__).parent.resolve()
BLD = SRC.joinpath("..", "..", "bld").resolve()
```

!!! note

```
If you want to know more about the "`src` layout" and why it is NASA-approved, read
[this article by Hynek Schlawack](https://hynek.me/articles/testing-packaging/) or this
[setuptools article](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout).
```

## The `bld` directory

The variable `BLD` defines the path to a build directory called `bld`. It is best
practice to store any outputs of the tasks in your project in a different folder than
`src`.

Whenever you want to regenerate your project, delete the build directory and rerun
pytask.

## Configuration Files

The configuration depends on your package manager choice. Each creates different files
to manage dependencies and project metadata.

=== "uv"

````
Create a `pyproject.toml` file for project configuration and dependencies:

``` { .toml .annotate }
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pytask"]

[build-system]
requires = ["uv_build"] # (1)!
build-backend = "uv_build"

[tool.pytask.ini_options]
paths = ["src/my_project"] # (2)!
```

1. `uv_build` provides the build backend for this minimal package layout.
2. `paths` tells pytask where to collect task modules.
````

=== "pixi"

````
Create a `pixi.toml` file for project configuration:

``` { .toml .annotate }
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.10"
channels = ["conda-forge"] # (1)!
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependencies]
pytask = "*"
python = ">=3.10"

[tool.pytask.ini_options]
paths = ["src/my_project"] # (2)!
```

1. `conda-forge` is the default package source for the pixi environment.
2. `paths` tells pytask where to collect task modules.
````

The `[tool.pytask.ini_options]` section tells pytask to look for tasks in
`src/my_project`. You will learn more about configuration in the
[configuration tutorial](configuration.md).

## The `.pytask` directory

The `.pytask` directory is where pytask stores its information. You do not need to
interact with it.

## Installation

=== "uv"

````
```console
$ uv sync
```

The command installs all packages. uv will ensure that all your dependencies are up-to-date.
````

=== "pixi"

````
```console
$ pixi install
```

pixi automatically creates the environment and installs dependencies. pixi will ensure that all your dependencies are up-to-date.
````
