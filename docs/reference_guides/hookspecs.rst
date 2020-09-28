Hook Specifications
===================

.. currentmodule:: _pytask.hookspecs

Hook specifications are the :term:`entry-points <entry-point>` provided by pytask to
change the behavior of the program.

The following sections provide an overview of the different phases while executing the
tasks the purpose of the entry-points.


Naming
------

The names of hooks always start with ``pytask_`` by convention. The following term
usually specifies the phase during the execution of tasks if there exist a group of hook
specifications.

If you encounter hooks which are suffixed with ``_protocol``, it means that subsequent
hooks are allowed to raise exceptions which are handled and stored in a report.


General
-------

.. autofunction:: pytask_add_hooks
   :noindex:


Command Line Interface
----------------------

.. autofunction:: pytask_extend_command_line_interface
   :noindex:


Configuration
-------------

.. autofunction:: pytask_configure
   :noindex:

.. autofunction:: pytask_parse_config
   :noindex:

.. autofunction:: pytask_post_parse
   :noindex:


Collection
----------

.. autofunction:: pytask_collect
   :noindex:

.. autofunction:: pytask_ignore_collect
   :noindex:

.. autofunction:: pytask_collect_modify_tasks
   :noindex:

.. autofunction:: pytask_collect_file_protocol
   :noindex:

.. autofunction:: pytask_collect_file
   :noindex:

.. autofunction:: pytask_collect_task_protocol
   :noindex:

.. autofunction:: pytask_collect_task_setup
   :noindex:

.. autofunction:: pytask_collect_task
   :noindex:

.. autofunction:: pytask_collect_task_teardown
   :noindex:

.. autofunction:: pytask_collect_node
   :noindex:

.. autofunction:: pytask_collect_log
   :noindex:


Parametrization
---------------

The hooks to parametrize a task are called during the collection when a function is
collected. Then, the function is duplicated according to the parametrization and the
duplicates are collected with :func:`pytask_collect_task`.

.. autofunction:: pytask_parametrize_task
   :noindex:

.. autofunction:: pytask_parametrize_kwarg_to_marker
   :noindex:


Execution
---------

.. autofunction:: pytask_execute
   :noindex:

.. autofunction:: pytask_execute_log_start
   :noindex:

.. autofunction:: pytask_execute_create_scheduler
   :noindex:

.. autofunction:: pytask_execute_build
   :noindex:

.. autofunction:: pytask_execute_task_protocol
   :noindex:

.. autofunction:: pytask_execute_task_log_start
   :noindex:

.. autofunction:: pytask_execute_task_setup
   :noindex:

.. autofunction:: pytask_execute_task
   :noindex:

.. autofunction:: pytask_execute_task_teardown
   :noindex:

.. autofunction:: pytask_execute_task_process_report
   :noindex:

.. autofunction:: pytask_execute_task_log_end
   :noindex:

.. autofunction:: pytask_execute_log_end
   :noindex:
