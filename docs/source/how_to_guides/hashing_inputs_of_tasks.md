# Hashing inputs of tasks

Any input to a task function is parsed by pytask's nodes. For example, `pathlib.Path`s
are parsed by \[`pytask.PathNode`\][]s. The \[`pytask.PathNode`\][] handles among other
things how changes in the underlying file are detected.

If an input is not parsed by any more specific node type, the general
\[`pytask.PythonNode`\][] is used.

In the following example, the argument `text` will be parsed as a
\[`pytask.PythonNode`\][].

```py
--8<-- "docs_src/how_to_guides/hashing_inputs_of_tasks_example_1_py310.py"
```

By default, pytask does not detect changes in \[`pytask.PythonNode`\][] and if the value
would change (without changing the task module), pytask would not rerun the task.

We can also hash the value of \[`pytask.PythonNode`\][] s so that pytask knows when the
input changed. For that, we need to use the \[`pytask.PythonNode`\][] explicitly and set
`hash = True`.

```py
--8<-- "docs_src/how_to_guides/hashing_inputs_of_tasks_example_2_py310.py"
```

When `hash=True`, pytask will call the builtin `hash` on the input that will call the
`__hash__()` method of the object.

Some objects like `tuple` and `typing.NamedTuple` are hashable and return correct hashes
by default.

```pycon
>>> hash((1, 2))
-3550055125485641917
```

`str` and `bytes` are special. They are hashable, but the hash changes from interpreter
session to interpreter session for security reasons (see `object.__hash__` for more
information). pytask will hash them using the `hashlib` module to create a stable hash.

```pycon
>>> from pytask import PythonNode
>>> node = PythonNode(value="Hello, World!", hash=True)
>>> node.state()
'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
```

`list` and `dict` are not hashable by default. Luckily, there are libraries who provide
this functionality like `deepdiff`. We can use them to pass a function to the
\[`pytask.PythonNode`\][] that generates a stable hash.

First, install `deepdiff`.

```console
$ uv add deepdiff
$ pixi add deepdiff
```

Then, create the hash function and pass it to the node. Make sure it returns either an
integer or a string.

```py
--8<-- "docs_src/how_to_guides/hashing_inputs_of_tasks_example_3_py310.py"
```
