# Extending pytask

pytask can be extended since it is built upon
[pluggy](https://pluggy.readthedocs.io/en/latest/), a [plugin](../glossary.md#plugin)
system for Python.

How does it work? Throughout the execution, pytask arrives at
[entry-points](../glossary.md#entry-point), called hook functions. When pytask calls a
hook function it loops through
[hook implementations](../glossary.md#hook-implementation) and each hook implementation
can alter the result of the entrypoint.

The full list of hook functions is specified in
[hookspecs](../reference_guides/hookspecs.md).

More general information about pluggy can be found in its
[documentation](https://pluggy.readthedocs.io/en/latest/).

There are two ways to add new
[hook implementations](../glossary.md#hook-implementation).

1. Using the `pytask build --hook-module` commandline option or the `hook_module`
    configuration value.
1. Packaging your [plugin](../glossary.md#plugin) as a Python package to publish and
    share it.

<a id="hook-module"></a>

## Using `--hook-module` and `hook_module`

The easiest and quickest way to extend pytask is to create a module, for example,
`hooks.py` and register it temporarily via the commandline option or permanently via the
configuration.

```console
pytask --hook-module hooks.py
```

or

```toml
[tool.pytask.ini_options]
hook_module = ["hooks.py"]
```

The value can be a path. If the path is relative it is assumed to be relative to the
configuration file or relative to the current working directory as a fallback.

The value can also be a module name. For example, if `hooks.py` lies your projects
package called `myproject` which is importable, then, you can also use

```toml
[tool.pytask.ini_options]
hook_module = ["myproject.hooks"]
```

In `hooks.py` we can add another commandline option to `pytask build` by providing an
additional [hook implementation](../glossary.md#hook-implementation) for the
[hook specification](../glossary.md#hook-specification)
`_pytask.hookspecs.pytask_extend_command_line_interface`.

```python
import click
from _pytask.pluginmanager import hookimpl


@hookimpl
def pytask_extend_command_line_interface(cli):
    """Add parameters to the command line interface."""
    cli.commands["build"].params.append(click.Option(["--hello"]))
```

## Packaging a plugin

### Preparation

Before you start implementing your plugin, the following notes may help you.

- [cookiecutter-pytask-plugin](https://github.com/pytask-dev/cookiecutter-pytask-plugin)
    is a template if you want to create a plugin.
- Check whether there exist plugins which offer similar functionality. For example, many
    plugins provide convenient interfaces to run another program with inputs via the
    command line. Naturally, there is a lot of overlap in the structure of the program
    and even the test battery. Finding the right plugin as a template may save you a lot
    of time.
- Make a list of hooks you want to implement. Think about how this plugin relates to
    functionality defined in pytask and other plugins. Maybe skim the documentation on
    [pluggy](../explanations/pluggy.md) to see whether there is advanced pattern which
    makes your implementation easier.
- File an issue on [Github](https://github.com/pytask-dev/pytask) and make a proposal
    for your plugin to get feedback from other developers. Your proposal should be
    concise and explain what problem you want to solve and how.

### Writing your plugin

This section explains some steps which are required for all plugins.

#### Set up the setuptools entry-point

pytask discovers plugins via `setuptools` [entry-points](../glossary.md#entry-point).
Following the approach advocated for by
[setuptools_scm](https://github.com/pypa/setuptools_scm), the entry-point is specified
in `pyproject.toml`.

```toml
[project]
name = "pytask-plugin"

[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]
namespaces = false

[project.entry-points.pytask]
pytask_plugin = "pytask_plugin.plugin"
```

For `setuptools_scm` you also need the following additions in `pyproject.toml`.

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.0"]

[tool.setuptools_scm]
write_to = "src/pytask_plugin/_version.py"
```

For a complete example with `setuptools_scm` and `pyproject.toml` see the
[pytask-parallel repo](https://github.com/pytask-dev/pytask-parallel/blob/main/pyproject.toml).

The entry-point for pytask is called `"pytask"` and points to a module called
`pytask_plugin.plugin`.

#### `plugin.py`

`plugin.py` is the [entry-point](../glossary.md#entry-point) for pytask to your package.
You can put all of your hook implementations in this module, but it is recommended to
imitate the structure of pytask and its modules. For example, all hook implementations
which change the configuration should be implemented in `pytask_plugin.config`.

If you follow the recommendations, the only content in `plugin.py` is a single hook
implementation which registers other hook implementations of your plugin. The following
example registers all hooks implemented in `config.py`.

```python
# Content of plugin.py

from pytask import hookimpl
from pytask_plugin import config


@hookimpl
def pytask_add_hooks(pm):
    pm.register(config)
```
