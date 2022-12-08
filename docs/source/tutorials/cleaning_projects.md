# Cleaning projects

Projects usually become cluttered with obsolete files after some time.

To clean the project, type `pytask clean`

```{include} ../_static/md/clean-dry-run.md
```

pytask performs a dry-run by default and lists all removable files.

If you want to remove the files, use {option}`pytask clean --mode` with one of the
following modes.

- `force` removes all files suggested in the `dry-run` without any confirmation.
- `interactive` allows you to decide for every file whether to keep it or not.

If you want to delete complete folders instead of single files, use
{option}`pytask clean --directories`.

```{include} ../_static/md/clean-dry-run-directories.md
```

## Excluding files

pytask excludes files that are under version control with git.

Use the {option}`pytask clean --exclude` option or the `exclude` key in the
configuration file to exclude files and directories.

Values can be Unix filename patterns that, for example, support the wildcard character
`*` for any characters. You find the documentation in {mod}`fnmatch`.

Here is an example for excluding a folder.

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
