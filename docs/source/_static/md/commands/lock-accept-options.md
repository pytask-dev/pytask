| Option                         | Default                                        | Description                                                                                                    |
| ------------------------------ | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `-k, --expression TEXT`        | -                                              | Select tasks by expression.                                                                                    |
| `-m, --marker-expression TEXT` | -                                              | Select tasks by marker expression.                                                                             |
| `--with-ancestors`             | `false`                                        | Also include preceding tasks of the selected tasks.                                                            |
| `--with-descendants`           | `false`                                        | Also include descending tasks of the selected tasks.                                                           |
| `--run-on TEXT`                | `task_change,dependency_change,product_change` | Choose which kinds of changes are considered when determining whether a task would normally require execution. |
| `--dry-run`                    | `false`                                        | Show which recorded states would be updated without writing changes.                                           |
| `-y, --yes`                    | `false`                                        | Apply the changes without prompting for confirmation.                                                          |
| `-h, --help`                   | -                                              | Show this message and exit.                                                                                    |
