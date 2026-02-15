# Debugging

Whenever you encounter an error in one of your tasks, pytask offers multiple ways which
help you to gain more information on the root cause.

## Post-mortem debugger

Using `pytask build --pdb` enables the post-mortem debugger. Whenever an exception is
raised inside a task, the prompt will enter the debugger enabling you to find out the
cause of the exception.

--8\<-- "docs/source/\_static/md/pdb.txt"

!!! tip

```
If you do not know about the Python debugger or pdb yet, check out this [explanation
from RealPython](https://realpython.com/python-debugging-pdb/).
```

!!! note

```
A following tutorial explains [how to select a subset of tasks](selecting_tasks.md).
Combine it with the `pytask build --pdb` flag to debug specific tasks.
```

## Tracing

If you want to enter the debugger at the start of every task, use
`pytask build --trace`.

--8\<-- "docs/source/\_static/md/trace.txt"

## Tracebacks

You can enrich the display of tracebacks by showing local variables in each stack frame.
Just execute `pytask build --show-locals`.

--8\<-- "docs/source/\_static/md/show-locals.txt"

## Custom debugger

If you want to use your custom debugger, make sure it is importable and use
`pytask build --pdbcls`. Here, we change the standard `pdb` debugger to IPython's
implementation.

```console
$ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
```
