# Cleaning projects

Projects usually become cluttered with obsolete files after some time.

To clean the project from files which are not recognized by pytask and type

```{image} /_static/images/clean-dry-run.svg
```

pytask performs a dry-run by default and shows all the files which can be removed.

If you want to remove the files, use {option}`pytask clean --mode` with one of the
following modes.

- `force` removes all files suggested in the `dry-run` without any confirmation.
- `interactive` allows you to decide for every file whether to keep it or not.

If you want to delete complete folders instead of single files, use
{option}`pytask clean --directories`. If all content in a directory can be removed, only
the directory is shown.

```{image} /_static/images/clean-dry-run-directories.svg
```

## Excluding files

Files which are under version control with git are excluded from the cleaning process.

If other files or directories should be excluded as well, you can use the
{option}`pytask clean --exclude` option or the `exclude` key in the configuration file.

The value can be a Unix filename pattern which is documented in {mod}`fnmatch` and
supports the wildcard character `*` for any characters and other symbols.

Here is an example where the `obsolete_folder` is excluded from the cleaning process.

```console
$ pytask clean --exclude obsolete_folder
```

or

```toml
[tool.pytask.ini_options]
exclude = ["obsolete_folder"]
```

## Further reading

- {doc}`../reference_guides/command_line_interface`.
