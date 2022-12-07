# Markers

pytask uses markers to attach additional information to a task. You can see all
available markers by using the `pytask markers` command.

```{include} ../_static/md/markers.md
```

You can use your markers to select tasks as explained in this {ref}`tutorial <markers>`.

If you create your marker, register it in the configuration file with its name and the
description.

```toml
[tool.pytask.ini_options.markers]
wip = "A marker for tasks which are work-in-progress."
```
