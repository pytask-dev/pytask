# Set up a project

To use pytask for larger projects, organize the project as a Python package. This
tutorial explains the minimal setup.

If you want to use pytask with a collection of scripts, you can skip this lesson and
move to the next section of the tutorials.

```{seealso}
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
{doc}`linked template or example project <../how_to_guides/bp_templates_and_projects>`.

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

```{seealso}
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

`````{tab-set}

````{tab-item} uv
:sync: uv

Create a `pyproject.toml` file for project configuration and dependencies:

```toml
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["pytask"]

[build-system]
requires = ["uv_build"]
build-backend = "uv_build"

[tool.pytask.ini_options]
paths = ["src/my_project"]
```

uv automatically handles build system configuration and package discovery.

````

````{tab-item} pixi
:sync: pixi

Create a `pixi.toml` file for project configuration:

```toml
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.9"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependencies]
pytask = "*"
python = ">=3.9"

[tool.pytask.ini_options]
paths = ["src/my_project"]
```

````

````{tab-item} pip
:sync: pip

Create a `pyproject.toml` file for project configuration:

```toml
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["pytask"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytask.ini_options]
paths = ["src/my_project"]
```

Also create a `requirements.txt` file:

```text
pytask
```

````

````{tab-item} conda/mamba
:sync: conda

Create an `environment.yml` file that includes the editable install:

```yaml
name: my_project
channels:
  - conda-forge
dependencies:
  - python>=3.9
  - pytask
  - pip
  - pip:
    - -e .
```

And a `pyproject.toml` file for project configuration:

```toml
[project]
name = "my_project"
version = "0.1.0"
requires-python = ">=3.9"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling"

[tool.pytask.ini_options]
paths = ["src/my_project"]
```

````
`````

The `[tool.pytask.ini_options]` section tells pytask to look for tasks in
`src/my_project`. You will learn more about configuration in the
{doc}`configuration tutorial <configuration>`.

## The `.pytask` directory

The `.pytask` directory is where pytask stores its information. You do not need to
interact with it.

## Installation

`````{tab-set}

````{tab-item} uv
:sync: uv

```console
$ uv sync
```

The command installs all packages. uv will ensure that all your dependencies are up-to-date.

````

````{tab-item} pixi
:sync: pixi

```console
$ pixi install
```

pixi automatically creates the environment and installs dependencies. pixi will ensure that all your dependencies are up-to-date.

````

````{tab-item} pip
:sync: pip

```console
$ pip install -e .
```

This creates an editable install where changes in the package's source files are immediately available in the installed version.

````

````{tab-item} conda/mamba
:sync: conda

```console
$ conda env create -f environment.yml
$ conda activate my_project
```

Or with mamba:

```console
$ mamba env create -f environment.yml
$ mamba activate my_project
```

The editable install is automatically handled by the `pip: -e .` entry in `environment.yml`.

````
`````
