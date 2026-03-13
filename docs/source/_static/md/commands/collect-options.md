| Option                     | Default | Description                                                                                                                                   |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `-c, --config FILE`        | -       | Path to configuration file.                                                                                                                   |
| `--database-url TEXT`      | -       | Url to the database.                                                                                                                          |
| `--editor-url-scheme TEXT` | `file`  | Use file, vscode, pycharm or a custom url scheme to add URLs to task ids to quickly jump to the task definition. Use no_link to disable URLs. |
| `--hook-module TEXT`       | -       | Path to a Python module that contains hook implementations.                                                                                   |
| `--ignore TEXT`            | -       | A pattern to ignore files or directories. Refer to 'pathlib.Path.match' for more info.                                                        |
| `-k EXPRESSION`            | -       | Select tasks via expressions on task ids.                                                                                                     |
| `-m MARKER_EXPRESSION`     | -       | Select tasks via marker expressions.                                                                                                          |
| `--nodes`                  | `false` | Show a task's dependencies and products.                                                                                                      |
| `--strict-markers`         | `false` | Raise errors for unknown markers.                                                                                                             |
| `-h, --help`               | -       | Show this message and exit.                                                                                                                   |
