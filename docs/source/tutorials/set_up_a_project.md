# Set up a project

This tutorial shows you how to set up your first project.

Use the
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project)
template to start right away.

Then, follow the tutorial to become familiar with its parts.

## The directory structure

The following directory tree is an example of how you can set up a project.

```
my_project
│
├───src
│   └───my_project
│       ├────config.py
│       └────...
│
├───setup.cfg
│
├───pyproject.toml
│
├───.pytask.sqlite3
│
└───bld
    └────...
```

### The configuration

The configuration resides in a `pyproject.toml` file in the project's root folder and
contains a `[tool.pytask.ini_options]` section.

```toml
[tool.pytask.ini_options]
paths = "src/my_project"
```

You do not have to add any configuration values, but you need the
`[tool.pytask.ini_options]` header. The header alone will signal pytask that this is the
project's root. pytask will store information it needs across executions in a
`.pytask.sqlite3` database next to the configuration file.

`paths` allows you to set the location of tasks when you do not pass them explicitly via
the CLI.

### The source directory

The `src` directory only contains a folder for the project in which the tasks and source
files reside. The nested structure is called the src layout and is the preferred way to
structure Python packages.

It also contains a `config.py` or a similar module to store the project's configuration.
For example, you should define paths pointing to the source and build directory of the
project.

```python
# Content of config.py.

from pathlib import Path


SRC = Path(__file__).parent.resolve()
BLD = SRC.joinpath("..", "..", "bld").resolve()
```

### The build directory

pytask creates the build directory `bld` during the execution for storing the products
of tasks. Delete it to rebuild the entire project.

### Install the project

Two files are necessary to turn the source directory into a Python package. It allows
performing imports from `my_project`. E.g., `from my_project.config import SRC`. We also
need `pip >= 21.1`.

First, we need a `setup.cfg` containing the name, the package version, and the source
code's location.

```ini
# Content of setup.cfg

[metadata]
name = my_project
version = 0.0.1

[options]
packages = find:
package_dir =
    =src

[options.packages.find]
where = src
```

Secondly, extend the `pyproject.toml` with this content:

```toml
# Content of pyproject.toml

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

:::{note}
If you used the
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project)
template, the two files would look slightly different since
[setuptools_scm](https://github.com/pypa/setuptools_scm) handles your versioning. Do not
change anything and proceed.
:::

Now, you can install the package into your environment with

```console
$ pip install -e .
```

This command will trigger an editable install of the project, which means any changes in
the package's source files are immediately available in the installed version.

:::{important}
Do not forget to rerun the editable install every time after you recreated your Python
environment.
:::

## Further Reading

- You can find more examples for structuring a research project in
  {doc}`../how_to_guides/bp_templates_and_projects`.
- [This article by Hynek Schlawack](https://hynek.me/articles/testing-packaging/)
  explains the `src` layout.
- You find this and more information in the documentation for
  [setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).
