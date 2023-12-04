# Set up a project

Assuming you want to use pytask for a more extensive project, you want
to organize the project as a Python package. This tutorial explains the minimal setup.

If you want to use pytask with a collection of scripts, you can skip this lesson
and move to the next section of the tutorials.

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

You can replicate the directory structure for your project or you start from pytask's
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

:::{seealso}
If you want to know more about the "`src` layout" and why it is NASA-approved, read
[this article by Hynek Schlawack](https://hynek.me/articles/testing-packaging/) or this
[setuptools article](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout).
:::

## The `bld` directory

The variable `BLD` defines the path to a build directory called `bld`. It is best
practice to store any outputs of the tasks in your project in a different folder than
`src`.

Whenever you want to regenerate your project, delete the build directory and rerun
pytask.

## `pyproject.toml`

The `pyproject.toml` file is the modern configuration file for most Python packages and
apps. It contains

1. the configuration for our Python package.
2. pytask's configuration.

Let us start with the configuration of the Python package, which contains general
information about the package, like its name and version, the definition of the package
folder, `src`.

```toml
[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "my_project"
version = "0.1.0"

[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]
namespaces = false
```

:::{seealso}
You can find more extensive information about this metadata in the documentation of
[setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).
:::

Alongside the package information, we include pytask's configuration under the
`[tool.pytask.ini_options]` section. We only tell pytask to look for tasks in
`src/my_project`.

```toml
[tool.pytask.ini_options]
paths = ["src/my_project"]
```

You will learn more about the configuration later in {doc}`tutorial <configuration>`.

You can copy the whole content of the `pyproject.toml` here.

<details>

```toml
[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "my_project"
version = "0.1.0"

[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]
namespaces = false

[tool.pytask.ini_options]
paths = ["src/my_project"]
```

</details>

## The `.pytask` directory

The `.pytask` directory is where pytask stores its information. You do not need to
interact with it.

## Installation

At last, you can install the package into your environment with

```console
$ pip install -e .
```

This command will trigger an editable install of the project, which is a development
mode and it means any changes in the package's source files are immediately available in
the installed version. Again, setuptools makes
[a good job explaining it](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

:::{important}
Do not forget to rerun the editable install every time after you recreate your Python
environment.

Also, do not mix it up with the regular installation command `pip install .` because it
will likely not work. Then, paths defined with the variables `SRC` and `BLD` in
`config.py` will look for files relative to the location where your package is installed
like `/home/user/miniconda3/envs/...` and not in the folder you are working in.
:::
