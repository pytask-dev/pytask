How to write a plugin
=====================

Since pytask is based on pluggy, it is extensible. In this section, you will learn some
key concepts you need to know to write a plugin. It won't deal with pluggy in detail,
but if you are interested feel free to read :ref:`pluggy`. A quick look at the first
paragraphs might be useful nonetheless.


Preparation
-----------

Before you start implementing your plugin, it makes sense to go through the following
steps.

- Check whether there exist plugins which offer similar functionality. For example, many
  plugins provide convenient interfaces to run another program with inputs via the
  command line. Naturally, there is a lot of overlap in the structure of the program and
  even the the test battery. Finding the right plugin as a template may save you a lot
  of time.

- Make a list of hooks you want to implement. Think about how this plugin relates to
  functionality defined in pytask and other plugins. Maybe skim the documentation on
  :ref:`pluggy` to see whether there is advanced pattern which makes your implementation
  easier.

- File an issue on `Github <https://github.com/pytask-dev/pytask>`_ and make a proposal
  for your plugin to get feedback from other developers. Your proposal should be concise
  and explain what problem you want to solve and how.


Writing your plugin
-------------------

This section explains some steps which are required for all plugins.


Set up the setuptools entry-point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pytask discovers plugins via ``setuptools`` entry-points. This is specified in
``setup.py``. See the following example.

.. code-block:: python

    # Content of setup.py

    from setuptools import find_packages
    from setuptools import setup

    setup(
        name="pytask-plugin",
        version="0.0.1",
        entry_points={"pytask": ["pytask_plugin = pytask_plugin.plugin"]},
        # PyPI classifier for pytask plugins
        classifiers=["Framework :: pytask"],
    )

The entry-point for pytask is called ``"pytask"`` and points to a module called
``pytask_plugin.plugin``.


plugin.py
~~~~~~~~~

``plugin.py`` is the main module in your package. You can put all of your hook
implementations in this module, but it is recommended imitate the structure of pytask
and its modules. For example, all hook implementations which change the configuration
should be implemented in ``pytask_plugin.config``.

If you follow the recommendations, the only content in ``plugin.py`` is a single hook
implementation which registers other hook implementations of your plugin. The following
example registers all hooks implemented in ``config.py``.

.. code-block:: python

    # Content of plugin.py

    import pytask
    from pytask_plugin import config


    @pytask.hookimpl
    def pytask_add_hooks(pm):
        pm.register(config)
