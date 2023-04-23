# Developer's Guide

## Testing

Run pytest to execute the test suite.

The test suite creates many temporary directories. There is usually a limit on the
number of open file descriptors on Unix systems which causes some tests and the end of
the test suite to fail. If that happens, increase the limit with the following command.

```console
$ ulimit -n 4096
```

## How to release

The following list covers all steps of a release cycle.

- Start a new release cycle by opening a milestone. Assign all relevant issues and merge
  requests to this milestone.

- Every change is pushed to the `main` branch of the repository and will make it into
  the next release.

- Once all additions to a release are merged, prepare `changes.rst` in the source folder
  of the documentation listing all changes which made it into the release.

- Update the version numbers in the animations if you create a new major or minor
  release.

- Go to the [release tab](https://github.com/pytask-dev/pytask/releases). Create a new
  release by clicking on "Draft a new release" and add a tag named `vx.x.x` on `main`
  and make it also the release title. Click on "Publish release".

  Creating a tag will trigger a pipeline which builds the package and uploads it to PyPI
  which consequently triggers a new release on conda-forge.

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

### `cProfile`

To profile pytask, you can follow this
[video](https://www.youtube.com/watch?v=qiZyDLEJHh0) (it also features explanations for
`git bisect`, caching, and profiling tools). We use {mod}`cProfile` with

```console
$ python -m cProfile -o log.pstats -m pytask directory/with/tasks
```

The profile can be visualized with

```console
$ pip install yelp-gprof2dot
$ gprof2dot log.pstats | dot -T svg -o out.svg
```

### `importtime`

To measure how long it takes to import pytask, use

```console
$ python -X importtime -c "import pytask"
```
