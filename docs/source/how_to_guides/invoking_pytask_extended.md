# Invoking pytask - Extended

## Entry-points

There are three entry-points to invoke pytask.

1. Use command line interface with

   ```console
   $ pytask
   ```

   Use the following flags to learn more about pytask and its configuration.

   ```console
   $ pytask --version
   $ pytask -h | --help
   ```

1. Invoke pytask via the Python interpreter which will add the current path to the
   `sys.path`.

   ```console
   python -m pytask /some/task/dir
   ```

1. Invoke pytask programmatically with

   ```python
   import pytask


   session = pytask.main({"paths": ...})
   ```

   Pass command line arguments with their long name and hyphens replaced by underscores
   as keys of the dictionary.

## Stopping after the first (N) failures

To stop the build of the project after the first (N) failures use

```console
$ pytask -x | --stop-after-first-failure  # Stop after the first failure
$ pytask --max-failures 2                 # Stop after the second failure
```
