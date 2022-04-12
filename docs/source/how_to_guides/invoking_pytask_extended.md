# Invoking pytask - Extended

In addition to the entrypoints explained in {doc}`../tutorials/invoking_pytask`, pytask
also has a rudimentary programmatic interface to the build command.

Invoke pytask programmatically with

```python
import pytask


session = pytask.main({"paths": ...})
```

Pass command line arguments with their long name and hyphens replaced by underscores as
keys of the dictionary.

The returned {class}`pytask.Session` object contains all the information of the executed
session and can be inspected.
