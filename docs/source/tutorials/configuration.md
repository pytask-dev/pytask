# Configuration

pytask can be configured via the command-line interface or permanently with a
configuration file.

## The configuration file

pytask accepts configurations in three files which are `pytask.ini`, `tox.ini` and
`setup.cfg`. Place a `[pytask]` section in those files and add your configuration below.

```ini
# Content of tox.ini

[pytask]
ignore =
    some_path
```

You can also leave the section empty. It will still have the benefit that pytask has a
stable root and will store the information about tasks, dependencies, and products in
the same directory as the configuration file in a database called `.pytask.sqlite3`.

## The location

There are two ways to find the configuration file when invoking pytask.

First, it is possible to pass the location of the configuration file via
{option}`pytask build -c` like

```console
$ pytask -c config/pytask.ini
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
