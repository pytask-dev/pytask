# Set up a project

This tutorial shows you how to set up your first project.

Use the
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project)
template to start right away.

Then, follow the tutorial to become familiar with its parts.

## The directory structure

The following directory tree is an example of how a project can be set up.

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

The configuration resides in a `pyproject.toml` file. The file is placed in the root
folder of the project and contains a `[tool.pytask.ini_options]` section.

```toml
[tool.pytask.ini_options]
paths = "src/my_project"
```

You can also leave the section empty. The header alone will signal pytask that this is
the root of the project. pytask will store information it needs across executions in a
`.pytask.sqlite3` database next to the configuration file.

`paths` allows you to set the location of tasks when you do not pass them explicitly via
the cli.

### The source directory

The `src` directory only contains a folder for the project in which the tasks and source
files of the project are placed. The nested structure is called the src layout and the
preferred way to structure Python packages.

It also contains a `config.py` or a similar module to store the configuration of the
project. For example, you should define paths pointing to the source and build directory
of the project.

```python
# Content of config.py.

from pathlib import Path


SRC = Path(__file__).parent.resolve()
BLD = SRC.joinpath("..", "..", "bld").resolve()
```

### The build directory

The build directory `bld` is created automatically during the execution. It is used to
store the products of tasks and can be deleted to rebuild the entire project.

### Install the project

Two files are necessary to turn the source directory into a Python package. It allows to
perform imports from `my_project`. E.g., `from my_project.config import SRC`. We also
need `pip >= 21.1`.

First, we need a `setup.cfg` which contains the name and version of the package and
where the source code can be found.

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

Now, you can install the package into your environment with

```console
$ pip install -e .
```

This command will trigger an editable install of the project which means any changes in
the source files of the package are immediately reflected in the installed version of
the package.

:::{important}
Do not forget to rerun the editable install should you recreate your Python environment.
:::

:::{tip}
For a more sophisticated setup where versions are managed via tags on the repository,
check out [setuptools_scm](https://github.com/pypa/setuptools_scm). The tool is also
used in
[cookiecutter-pytask-project](https://github.com/pytask-dev/cookiecutter-pytask-project).
:::

## Further Reading

- You can find more examples for structuring a research project in
  {doc}`../how_to_guides/bp_templates_and_projects`.
- An explanation for the src layout can be found in [this article by Hynek
  Schlawack](https://hynek.me/articles/testing-packaging/).
- You find this and more information in the documentation for
  [setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).
