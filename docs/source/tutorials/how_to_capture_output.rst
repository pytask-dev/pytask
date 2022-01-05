How to capture output
=====================

What is capturing? Some of your tasks may use ``print`` statements, have progress bars,
require user input or the libraries you are using show information during execution.

Since the output would pollute the terminal and the information shown by pytask, it
captures all the output during execution and attaches it to the report of this task by
default.

If the task fails, the output is shown along with the traceback to help you track down
the error.


Default stdout/stderr/stdin capturing behavior
----------------------------------------------

During task execution any output sent to ``stdout`` and ``stderr`` is captured. If a
task fails its captured output will usually be shown along with the failure traceback.

In addition, ``stdin`` is set to a "null" object which will fail on attempts to read
from it because it is rarely desired to wait for interactive input when running
automated tasks.

By default capturing is done by intercepting writes to low level file descriptors. This
allows to capture output from simple ``print`` statements as well as output from a
subprocess started by a task.


Setting capturing methods or disabling capturing
------------------------------------------------

There are three ways in which ``pytask`` can perform capturing:

* ``fd`` (file descriptor) level capturing (default): All writes going to the operating
  system file descriptors 1 and 2 will be captured.

* ``sys`` level capturing: Only writes to Python files ``sys.stdout`` and ``sys.stderr``
  will be captured.  No capturing of writes to file descriptors is performed.

* ``tee-sys`` capturing: Python writes to ``sys.stdout`` and ``sys.stderr`` will be
  captured, however the writes will also be passed-through to the actual ``sys.stdout``
  and ``sys.stderr``.

You can influence output capturing mechanisms from the command line:

.. code-block:: console

    pytask -s                  # disable all capturing
    pytask --capture=sys       # replace sys.stdout/stderr with in-mem files
    pytask --capture=fd        # also point filedescriptors 1 and 2 to temp file
    pytask --capture=tee-sys   # combines 'sys' and '-s', capturing sys.stdout/stderr
                               # and passing it along to the actual sys.stdout/stderr


Using print statements for debugging
------------------------------------

One primary benefit of the default capturing of stdout/stderr output is that you can use
print statements for debugging:

.. code-block:: python

    # content of task_capture.py


    def task_func1():
        assert True


    def task_func2():
        print("Debug statement")
        assert False

and running this module will show you precisely the output of the failing function and
hide the other one:

.. code-block:: console

    $ pytask -s
    ========================= Start pytask session =========================
    Platform: win32 -- Python 3.x.x, pytask 0.x.x, pluggy 0.13.x
    Root: .
    Collected 2 task(s).

    F.
    =============================== Failures ===============================
    _________________ Task task_capture.py::task_func2 failed ______________

    Traceback (most recent call last):
      File "task_capture.py", line 7, in task_func2
        assert False
    AssertionError

    ---------------------- Captured stdout during call ---------------------
    Debug statement.

    ==================== 1 succeeded, 1 failed in 0.01s ====================
