# Using workspaces

There are situations where you want to structure your project as a multi-package
workspace. Reasons are

- You are developing a scientific package alongside the project that you want to publish
  later.
- The code for dealing with the dataset should be reused in other projects.
- You want to strictly separate the pytask tasks from the remaining code to be able to
  switch to another build system.

In those instances, a workspace might be the right choice.

```text
project
├── packages
│   ├── data
│   │   ├── pyproject.toml
│   │   └── src
│   │       └── data
│   │           ├── __init__.py
│   │           └── ...
│   ├── analysis
│   │   ├── pyproject.toml
│   │   └── src
│   │       └── analysis
│   │           ├── __init__.py
│   │           └── ...
│   └── tasks
│       ├── pyproject.toml
│       └── src
│           └── tasks
│               ├── __init__.py
│               └── ...
│
├── pyproject.toml
├── README.md
├── ...
```

## Using workspaces with uv

uv provides excellent support for workspaces which you can read more about in the
[uv documentation](https://docs.astral.sh/uv/concepts/projects/workspaces).

## Using workspaces with pixi

pixi is still working on a native workspace experience, but there are workarounds.

- [https://pixi.sh/latest/build/workspace/](https://pixi.sh/latest/build/workspace/)
- [https://github.com/prefix-dev/pixi/discussions/387](https://github.com/prefix-dev/pixi/discussions/387)
- [https://github.com/Andre-Medina/python-pixi-mono-template](https://github.com/Andre-Medina/python-pixi-mono-template)
