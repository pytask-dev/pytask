import functools
import pdb
import traceback

import pytask


@pytask.hookimpl(hookwrapper=True)
def pytask_execute_task(task):
    if hasattr(task, "function"):
        task.function = wrap_function_for_post_mortem_debugging(task.function)
    yield


def wrap_function_for_post_mortem_debugging(function):
    @functools.wraps(function)
    def wrapper():
        try:
            function()
        except Exception as e:
            traceback.print_exc()
            pdb.post_mortem()
            raise e

    return wrapper
