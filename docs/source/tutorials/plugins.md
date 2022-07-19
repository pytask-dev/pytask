# Plugins

Users employ pytask in many different contexts, making it impossible for pytask's
maintainers to support all possible use-cases.

Therefore, pytask uses [pluggy](https://github.com/pytest-dev/pluggy), a plugin
framework, for allowing users to extend pytask.

## Where to find plugins

You can find plugins in many places.

- All plugins should appear in this {doc}`automatically updated list <../plugin_list>`,
  which is created by scanning packages on PyPI.
- Check out the repositories in the [pytask-dev](https://github.com/pytask-dev) Github
  organization for a collection of officially supported plugins.
- Check out the [pytask Github topic](https://github.com/topics/pytask), which shows an
  overview of repositories linked to pytask.
- Search on [anaconda.org](https://anaconda.org/search?q=pytask) for related packages.

## How to implement your plugin

Follow the {doc}`guide on writing a plugin <../how_to_guides/how_to_write_a_plugin>` to
write your own plugin.
