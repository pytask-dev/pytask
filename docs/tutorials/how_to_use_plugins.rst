How to use plugins
==================

Since build systems are deployed in many different contexts, all possible applications
are unforeseeable and cannot be directly supported by pytask's developers.

For that reason, pytask is built upon `pluggy <https://github.com/pytest-dev/pluggy>`_,
a plugin framework also used in pytest which allows to extend pytask's capabilities with
plugins.


Where to find plugins
---------------------

Plugins can be found in many places.

- Check out the repositories in the `pytask-dev <https://github.com/pytask-dev>`_ Github
  organization which includes a collection of officially supported plugins.

- Check out the `pytask Github topic <https://github.com/topics/pytask>`_ which shows an
  overview of repositories linked to pytask.

- Search on `anaconda.org <https://anaconda.org/search?q=pytask>`_ for related packages.


How to use plugins
------------------

To use a plugin, simply follow the installation instructions. A plugin will enable
itself by using pytask's entry-point.


How to implement your own plugin
--------------------------------

Follow the :doc:`guide on writing a plugin <../how_to_guides/how_to_write_a_plugin.rst>`
to write your own plugin.
