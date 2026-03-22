| Option                     | Default | Description                                                                                                                                   |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `-c, --config FILE`        | -       | Path to configuration file.                                                                                                                   |
| `-d, --directories`        | `false` | Remove whole directories.                                                                                                                     |
| `--database-url TEXT`      | -       | Url to the database.                                                                                                                          |
| `-e, --exclude PATTERN`    | -       | A filename pattern to exclude files from the cleaning process.                                                                                |
| `--editor-url-scheme TEXT` | `file`  | Use file, vscode, pycharm or a custom url scheme to add URLs to task ids to quickly jump to the task definition. Use no_link to disable URLs. |
| `--hook-module TEXT`       | -       | Path to a Python module that contains hook implementations.                                                                                   |
| `--ignore TEXT`            | -       | A pattern to ignore files or directories. Refer to 'pathlib.Path.match' for more info.                                                        |
| `-k EXPRESSION`            | -       | Select tasks via expressions on task ids.                                                                                                     |
| `-m MARKER_EXPRESSION`     | -       | Select tasks via marker expressions.                                                                                                          |
| \`--mode \[dry-run         | force   | interactive\]\`                                                                                                                               |
| `-q, --quiet`              | `false` | Do not print the names of the removed paths.                                                                                                  |
| `--strict-markers`         | `false` | Raise errors for unknown markers.                                                                                                             |
| `-h, --help`               | -       | Show this message and exit.                                                                                                                   |
