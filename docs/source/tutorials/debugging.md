# Debugging

Whenever you encounter an error in one of your tasks, pytask offers multiple ways which
help you to gain more information on the root cause.

## Post-mortem debugger

Using {option}`pytask build --pdb` enables the post-mortem debugger. Whenever an
exception is raised inside a task, the prompt will enter the debugger enabling you to
find out the cause of the exception.

```{include} ../_static/md/pdb.md
```

:::{tip}
If you do not know about the Python debugger or pdb yet, check out this [explanation
from RealPython](https://realpython.com/python-debugging-pdb/).
:::

:::{note}
A following tutorial explains {doc}`how to select a subset of tasks <selecting_tasks>`.
Combine it with the {option}`pytask build --pdb` flag to debug specific tasks.
:::

## Tracing

If you want to enter the debugger at the start of every task, use
{option}`pytask build --trace`.

```{include} ../_static/md/trace.md
```

## Tracebacks

You can enrich the display of tracebacks by showing local variables in each stack frame.
Just execute {option}`pytask build --show-locals`.

```{include} ../_static/md/show-locals.md
```

## Custom debugger

If you want to use your custom debugger, make sure it is importable and use
{option}`pytask build --pdbcls`. Here, we change the standard `pdb` debugger to
IPython's implementation.

```console
$ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
```
