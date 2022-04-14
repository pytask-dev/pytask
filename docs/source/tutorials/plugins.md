# Plugins

Since pytask is used in many different contexts, all possible applications are
unforeseeable and cannot be directly supported by pytask's developers.

Therefore, pytask is built upon [pluggy](https://github.com/pytest-dev/pluggy), a plugin
framework also used in pytest which allows other developers to extend pytask.

## Where to find plugins

Plugins can be found in many places.

- All plugins should appear in this {doc}`automatically updated list <../plugin_list>`
  which is created by scanning packages on PyPI.
- Check out the repositories in the [pytask-dev](https://github.com/pytask-dev) Github
  organization for a collection of officially supported plugins.
- Check out the [pytask Github topic](https://github.com/topics/pytask) which shows an
  overview of repositories linked to pytask.
- Search on [anaconda.org](https://anaconda.org/search?q=pytask) for related packages.

## How to implement your own plugin

Follow the {doc}`guide on writing a plugin <../how_to_guides/how_to_write_a_plugin>` to
write your own plugin.
