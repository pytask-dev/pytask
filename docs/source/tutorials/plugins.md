# Plugins

Users employ pytask in many different contexts, making it impossible for pytask's
maintainers to cater to all possible use cases.

Therefore, pytask uses [pluggy](https://github.com/pytest-dev/pluggy), a plugin
framework, to allow users to extend pytask.

## Where can I find plugins?

You can find plugins in many places.

- All plugins should appear in this {doc}`automatically updated list <../plugin_list>`,
  which is created by scanning packages on PyPI.
- Check out the repositories in the [pytask-dev](https://github.com/pytask-dev) Github
  organization for a collection of officially supported plugins.
- Check out the [pytask Github topic](https://github.com/topics/pytask), which shows an
  overview of repositories linked to pytask.
- Search on [anaconda.org](https://anaconda.org/search?q=pytask) or
  [prefix.dev](https://prefix.dev) for related packages.

## How to extend pytask

Follow the {doc}`guide on extending pytask <../how_to_guides/extending_pytask>` to add
your own hook implementations or write your plugin.
