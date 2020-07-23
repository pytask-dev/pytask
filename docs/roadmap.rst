Roadmap
=======

More executors or builders
--------------------------

* ~R based on rpy2.~

* Julia based on `pyjulia <https://github.com/JuliaPy/pyjulia>`_.

These two examples can make use of the APIs which are provided for Python. Thus, it
is not strictly necessary to immediately write a plugin for them :). It would be
extremely useful if debugging would work seamlessly - a debug statement in a Julia
script trickles down to Python, etc..

* ~LaTeX (see `cook <https://github.com/jachris/cook/blob/master/cook/latex.py>`_).~

* A file downloader (detect whether online file has been modified, resuming of
  downloads, etc.)

* Shell, Bash, CMD, Powershell

I imagine the latter three to provide two interfaces where the first one may look like
this.

.. code-block:: python

    import pytask


    @pytask.mark.download_file(some_url)
    @pytask.mark.produces("path/to/downloaded_file.csv")
    def task_download_file():
        pass

The download marker passes information about the remote files. There might be other
decorators as well for directories and so on. The function is only a dummy function
since it will be replaced by the plugin. This would allow the plugin to handle many
things without having the user to know about.

* Checking whether the remote file has changed and needs to be re-downloaded.
* Resuming downloads.
* Validation via hashes?

The second interface is more low-level and provides some helpers which can be used
inside a custom function.


Persisting tasks
----------------

Sometimes you have expensive tasks and do not want to re-run them unless something
important has changed and not because ``black`` formatted the task.

Implement a ``@pytask.mark.persist`` decorator which skip tasks as long as there
products exist and they are unchanged from the time they were produced.

It is similar to the skip decorator, but the skip decorator will also skip all following
tasks.
