# Configuration

pytask can be configured via the command-line interface or permanently with a
`pyproject.toml` file.

The file also indicates the root of your project, where pytask stores information in a
`.pytask` folder.

## The configuration file

You only need to add the header to the configuration file to indicate the root of your
project.

```toml title="pyproject.toml"
[tool.pytask.ini_options]
```

We can also overwrite pytask's behavior of collecting tasks from the current working
directory and, instead, search for paths in a directory called `src` next to the
configuration file.

```toml title="pyproject.toml"
[tool.pytask.ini_options]
paths = ["src"]
```

## The location

There are two ways to point pytask to the configuration file.

The first option is to let pytask try to find the configuration itself.

1. Find the common directory of all paths passed to pytask (default to the current
    working directory).
1. Look at all parent directories from this directory and return the file if it exists.
1. Stop searching if a directory contains a `.git` directory/file or a valid
    configuration file with the correct section.

Secondly, it is possible to pass the location of the configuration file via
`pytask build -c` like

```console
$ pytask -c config/pyproject.toml
```

## The options

All possible configuration values are found in the
[reference guide on the configuration](../reference_guides/configuration.md).
