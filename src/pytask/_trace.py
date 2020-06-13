import functools
import pdb

import pytask


@pytask.hookimpl(hookwrapper=True)
def pytask_execute_task(task):
    if hasattr(task, "function"):
        task.function = wrap_function_for_tracing(task.function)
    yield


def wrap_function_for_tracing(function):
    @functools.wraps(function)
    def wrapper():
        pdb.runcall(function)

    return wrapper
