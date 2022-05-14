# SVGs

This folder contains scripts to create svgs for the documentation and other publicly
available material.

## Setup

Before creating the SVGs, you need to adjust the version of pytask from a dirty version
to the desired one.

Set `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTASK` to the desired version.

```console
# Command for Powershell
$ $env:SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTASK = "v0.2.0"

# Command for Bash
$ export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTASK = "v0.2.0"
```

## Post-processing of SVGs

- [ ] Remove flickering left-overs.
- [ ] Set Python version to 3.10.0.
- [ ] Set pluggy version to 1.0.0.
- [ ] Set root path to C:\\Users\\tobias\\git\\pytask-examples.

## Store

Store image in docs/source/\_static/images/.
