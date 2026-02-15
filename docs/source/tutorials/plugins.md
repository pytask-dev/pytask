# Plugins

Users employ pytask in many different contexts, making it impossible for pytask's
maintainers to cater to all possible use cases.

Therefore, pytask uses [pluggy](https://github.com/pytest-dev/pluggy), a
[plugin](../glossary.md#plugin) framework, to allow users to extend pytask.

## How to extend pytask

A quick method to extend pytask is explained in the
[guide on extending pytask](../how_to_guides/extending_pytask.md). You will learn how to
add your own [hook implementations](../glossary.md#hook-implementation) or write your
[plugin](../glossary.md#plugin).

## Where can I find plugins?

You can find plugins in many places.

- All plugins should appear in this [automatically updated list](../plugin_list.md),
    which is created by scanning packages on PyPI.
- Check out the repositories in the [pytask-dev](https://github.com/pytask-dev) Github
    organization for a collection of officially supported plugins.
- Check out the [pytask Github topic](https://github.com/topics/pytask), which shows an
    overview of repositories linked to pytask.
- Search on [anaconda.org](https://anaconda.org/search?q=pytask) or
    [prefix.dev](https://prefix.dev) for related packages.
