# Hashing inputs of tasks

Any input to a task function is parsed by pytask's nodes. For example,
{class}`pathlib.Path`s are parsed by {class}`~pytask.PathNode`s. The
{class}`~pytask.PathNode` handles among other things how changes in the underlying file
are detected.

If an input is not parsed by any more specific node type, the general
{class}`~pytask.PythonNode` is used.

In the following example, the argument `text` will be parsed as a
{class}`~pytask.PythonNode`.

```{literalinclude} ../../../docs_src/how_to_guides/hashing_inputs_of_tasks_example_1_py310.py
```

By default, pytask does not detect changes in {class}`~pytask.PythonNode` and if the
value would change (without changing the task module), pytask would not rerun the task.

We can also hash the value of {class}`~pytask.PythonNode` s so that pytask knows when
the input changed. For that, we need to use the {class}`~pytask.PythonNode` explicitly
and set `hash = True`.

```{literalinclude} ../../../docs_src/how_to_guides/hashing_inputs_of_tasks_example_2_py310.py
```

When `hash=True`, pytask will call the builtin {func}`hash` on the input that will call
the `__hash__()` method of the object.

Some objects like {class}`tuple` and {class}`typing.NamedTuple` are hashable and return
correct hashes by default.

```pycon
>>> hash((1, 2))
-3550055125485641917
```

{class}`str` and {class}`bytes` are special. They are hashable, but the hash changes
from interpreter session to interpreter session for security reasons (see
{meth}`object.__hash__` for more information). pytask will hash them using the
{mod}`hashlib` module to create a stable hash.

```pycon
>>> from pytask import PythonNode
>>> node = PythonNode(value="Hello, World!", hash=True)
>>> node.state()
'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
```

{class}`list` and {class}`dict` are not hashable by default. Luckily, there are
libraries who provide this functionality like `deepdiff`. We can use them to pass a
function to the {class}`~pytask.PythonNode` that generates a stable hash.

First, install `deepdiff`.

```console
$ uv add deepdiff
$ pixi add deepdiff
```

Then, create the hash function and pass it to the node. Make sure it returns either an
integer or a string.

```{literalinclude} ../../../docs_src/how_to_guides/hashing_inputs_of_tasks_example_3_py310.py
```
