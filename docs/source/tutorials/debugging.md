# Debugging

Whenever you encounter an error in one of your tasks, pytask offers multiple ways which
help you to gain more information on the root cause.

## Post-mortem debugger

Using {confval}`pytask build --pdb` enables the post-mortem debugger. Whenever an
exception is raised inside a task, the prompt will enter the debugger enabling you to
find out the cause of the exception.

```{image} /_static/images/pdb.svg
```

A following tutorial explains {doc}`how to select a subset of tasks <selecting_tasks>`.
Combine it with the {option}`pytask build --pdb` flag to debug specific tasks.

## Tracing

If you want to enter the debugger at the start of every task, use
{option}`pytask build --trace`.

```{image} /_static/images/trace.svg
```

## Tracebacks

You can enrich the display of tracebacks by showing local variables in each stack frame.
Just execute {option}`pytask build --show-locals`.

```{image} /_static/images/show-locals.svg
```

## Custom debugger

If you want to use your custom debugger, make sure it is importable and use
{option}`pytask build --pdbcls`. Here, we change the standard `pdb` debugger to
IPython's implementation.

```console
$ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
```
