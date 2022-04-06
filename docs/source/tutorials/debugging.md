# Debugging

Whenever you encounter an error in one of your tasks, pytask offers multiple ways which
help you to gain more information on the root cause.

Through quick and easy feedback you are more productive and gain more confidence in your
code.

## Tracebacks

You can enrich the display of tracebacks by showing local variables in each stack frame.
Just execute pytask with {confval}`show_locals`, meaning `pytask --show-locals`.

```{image} /_static/images/show-locals.svg
```

## Debugging

Using {confval}`pdb` enables the post-mortem debugger. Whenever an exception is raised
inside a task, the prompt will enter the debugger enabling you to find out the cause of
the exception.

```{image} /_static/images/pdb.svg
```

:::{seealso}
{doc}`A following tutorial <selecting_tasks>` shows you how to run only one or a subset
of tasks which can be combined with the debug mode.
:::

## Tracing

If you want to enter the debugger at the start of every task, use {confval}`trace`.

```{image} /_static/images/trace.svg
```

## Custom debugger

If you want to use your custom debugger, make sure it is importable and use
{option}`pytask build --pdbcls`. Here, we change the standard `pdb` debugger to
IPython's implementation.

```console
$ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
```
