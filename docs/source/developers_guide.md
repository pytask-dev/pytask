# Developer's Guide

## How to release

The following list covers all steps of a release cycle.

- Start a new release cycle by opening a milestone. Assign all relevant issues and merge
  requests to this milestone.

- Every change is pushed to the `main` branch of the repository and will make it into
  the next release.

- Once all additions to a release are merged, prepare `changes.rst` in the source
  folder of the documentation listing all changes which made it into the release.

- Go to the [release tab](https://github.com/pytask-dev/pytask/releases). Create a new
  release by clicking on "Draft a new release" and add a tag named `vx.x.x` on
  `main` and make it also the release title. Click on "Publish release".

  Creating a tag will trigger a pipeline which builds the package and uploads it to
  PyPI which consequently triggers a new release on conda-forge.

## Creating showcases on the command line

- Replace prompt in powershell core with a simple arrow by typing

  ```console
  $ function prompt {"> "}
  ```

- Rename the tab with

  ```console
  $ $Host.UI.RawUI.WindowTitle = $title
  ```

## Profiling the application

To profile pytask, you can follow this [video](https://www.youtube.com/watch?v=qiZyDLEJHh0) (it also features explanations for `git
bisect`, caching, and profiling tools). We use {mod}`cProfile` with

```console
$ python -m cProfile -o log.pstats pytask directory/with/tasks
```

The profile can be visualized with

```console
$ pip install yelp-gprof2dot
$ gprof2dot log.pstats | dot -T svg -o out.svg
```
