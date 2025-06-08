# Installation

<!-- Keep in sync with README.md -->

pytask is available on [PyPI](https://pypi.org/project/pytask) and
[conda-forge](https://anaconda.org/conda-forge/pytask).

## Recommended

We recommend using modern package managers for faster and more reliable dependency
management:

```console
$ uv add pytask
```

or

```console
$ pixi add pytask
```

Learn more about [uv](https://docs.astral.sh/uv/) and [pixi](https://pixi.sh/).

## Traditional

You can also install pytask using traditional package managers:

```console
$ pip install pytask
```

or

```console
$ conda install -c conda-forge pytask
```

<!-- END: Keep in sync with README.md -->

Verify the installation by displaying the help page listing all available commands and
some options.

```{include} ../_static/md/help-page.md
```

For command-specific help, type

```console
$ pytask <command-name> --help
```

Non-Windows platforms have automatic color support. On Windows, use
[Windows Terminal](https://github.com/microsoft/terminal), which you can install from
the [Microsoft Store](https://aka.ms/terminal).
