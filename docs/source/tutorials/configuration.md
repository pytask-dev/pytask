# Configuration

pytask can be configured via the command-line interface or permanently with a
`pyproject.toml` file.

The file also indicates the root of your project where pytask stores information in a
`.pytask.sqlite3` database.

## The configuration file

You only need to add the header to the configuration file to indicate the root of your
project.

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
   it exists.
3. Stop searching if a directory contains a `.git` directory/file or a valid configuration file with
   the right section.

## The options

You can find all possible configuration values in the
{doc}`reference guide on the configuration <../reference_guides/configuration>`.
