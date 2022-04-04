# Configuration

pytask can be configured via the command-line interface or permanently with a
`pyproject.toml` file.

The file also indicates the root of your project where pytask stores information on
whether tasks need to be executed or not in a `.pytask.sqlite3` database.

:::{important}
pytask.ini, tox.ini, and setup.cfg will be deprecated as configuration files for pytask
starting with v0.3 or v1.0. Switch to a `pyproject.toml` file! If you execute pytask
with an old configuration file, pytask provides you with a copy-paste snippet of your
configuration in the `toml` format to facilitate the transition.
:::

## The configuration file

You only need to add the header to the configuration file if you want to indicate the
root of your project.

```toml
[tool.pytask.ini_options]
```

We can also overwrite pytask's behavior of collecting tasks from the current working
directory and, instead, search for paths in a directory called `src` next to the
configuration file.

```toml
[tool.pytask.ini_options]
paths = "src"
```

## The location

There are two ways to point pytask to the configuration file.

First, it is possible to pass the location of the configuration file via
{option}`pytask build -c` like

```console
$ pytask -c config/pyproject.toml
```

The second option is to let pytask try to find the configuration itself.

1. Find the common base directory of all paths passed to pytask (default to the current
   working directory).
2. Starting from this directory, look at all parent directories, and return the file if
   it is found.
3. If a directory contains a `.git` directory/file, a `.hg` directory or a valid
   configuration file with the right section stop searching.

## The options

You can find all possible configuration values in the
{doc}`reference guide on the configuration <../reference_guides/configuration>`.
