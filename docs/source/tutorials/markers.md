# Markers

pytask uses markers to attach additional information to a task. You can see all
available markers by using the `pytask markers` command.

```{include} ../_static/md/markers.md
```

As explained in this {ref}`tutorial <markers>`, you can use markers to select tasks.

Register your marker in the configuration file with its name and description.

```toml
[tool.pytask.ini_options.markers]
wip = "A marker for tasks which are work-in-progress."
```
