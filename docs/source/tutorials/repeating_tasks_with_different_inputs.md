# Repeating tasks with different inputs

Do you want to repeat a task over a range of inputs? Loop over your task function!

## An example

We reuse the task from the previous [tutorial](write_a_task.md), which generates random
data and repeat the same operation over several seeds to receive multiple, reproducible
samples.

Apply the `@task` decorator, loop over the function and supply different seeds and
output paths as default arguments of the function.

=== "Annotated"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs1_py310.py"
```
````

=== "produces"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs1_produces.py"
```
````

Executing pytask gives you this:

--8<-- "docs/source/_static/md/repeating-tasks.md"

## Dependencies

You can also add dependencies to repeated tasks just like with any other task.

=== "Annotated"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs2_py310.py"
```
````

=== "produces"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs2_produces.py"
```
````

<a id="how-to-repeat-a-task-with-different-inputs-the-id"></a>

## The id

Every task has a unique id that can be used to [select it](selecting_tasks.md). The
standard id combines the path to the module where the task is defined, a double colon,
and the name of the task function. Here is an example.

```text
../task_data_preparation.py::task_create_random_data
```

This behavior would produce duplicate ids for parametrized tasks. By default,
auto-generated ids are used.

<a id="auto-generated-ids"></a>

### Auto-generated ids

pytask constructs ids by extending the task name with representations of the values used
for each iteration. Booleans, floats, integers, and strings enter the task id directly.
For example, a task function that receives four arguments, `True`, `1.0`, `2`, and
`"hello"`, one of each data type, has the following id.

```
task_data_preparation.py::task_create_random_data[True-1.0-2-hello]
```

Arguments with other data types cannot be converted to strings and, thus, are replaced
with a combination of the argument name and the iteration counter.

For example, the following function is parametrized with tuples.

=== "Annotated"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs3_py310.py"
```
````

=== "produces"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs3_produces.py"
```
````

Since the tuples are not converted to strings, the ids of the two tasks are

```text
task_data_preparation.py::task_create_random_data[seed0]
task_data_preparation.py::task_create_random_data[seed1]
```

<a id="ids"></a>

### User-defined ids

The `@task` decorator has an `id` keyword, allowing the user to set a unique name for
the iteration.

=== "Annotated"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs4_py310.py"
```
````

=== "produces"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs4_produces.py"
```
````

produces these ids

```text
task_data_preparation.py::task_create_random_data[first]
task_data_preparation.py::task_create_random_data[second]
```

## Complex example

Parametrizations are becoming more complex quickly. Often, there are many tasks with ids
and arguments. Here are three tips to organize the repetitions.

1. Use suitable containers to organize your ids and the function arguments.

**NamedTuple**

`typing.NamedTuple` or `collections.namedtuple` are useful containers to organize the
arguments of the parametrizations. They also provide better support for heterogeneous
types than dictionaries.

```python
from pathlib import Path
from typing import NamedTuple


class Arguments(NamedTuple):
    seed: int
    path_to_data: Path


ID_TO_KWARGS = {
    "first": Arguments(seed=0, path_to_data=Path("data_0.pkl")),
    "second": Arguments(seed=1, path_to_data=Path("data_1.pkl")),
}
```

**Dictionary**

```python
ID_TO_KWARGS = {
    "first": {"seed": 0, "produces": "data_0.pkl"},
    "second": {"seed": 1, "produces": "data_1.pkl"},
}
```

1. `@task` has a `kwargs` argument that allows you inject arguments to the function
    instead of adding them as default arguments.

1. If the generation of arguments for the task function is complex, we should use a
    function.

Following these three tips, the parametrization becomes

=== "Annotated"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs5_py310.py"
```
````

=== "produces"

````
```py
--8<-- "docs_src/tutorials/repeating_tasks_with_different_inputs5_produces.py"
```
````

Unpacking all the arguments can become tedious. Instead, use the `kwargs` argument of
the `@task` decorator to pass keyword arguments to the task.

```python
for id_, kwargs in ID_TO_KWARGS.items():

    @task(id=id_, kwargs=kwargs)
    def task_create_random_data(seed, produces): ...
```

Writing a function that creates `ID_TO_KWARGS` would be even more pythonic.

```python
def create_parametrization():
    id_to_kwargs = {}
    for i, id_ in enumerate(["first", "second"]):
        id_to_kwargs[id_] = {"produces": f"out_{i}.txt"}

    return id_to_kwargs


ID_TO_KWARGS = create_parametrization()


for id_, kwargs in ID_TO_KWARGS.items():

    @task(id=id_, kwargs=kwargs)
    def task_create_random_data(i, produces): ...
```

The
[best-practices guide on parametrizations](../how_to_guides/bp_complex_task_repetitions.md)
goes into even more detail on how to scale parametrizations.

## A warning on globals

The following example warns against accidentally using running variables in your task
definition.

You won't encounter these problems if you strictly use the below-mentioned interfaces.

Look at this repeated task, which runs three times and tries to produce a text file with
some content.

```python
from pytask import Product
from pytask import task
from pathlib import Path


for i in range(3):

    @task
    def task_example(path: Annotated[Path, Product] = Path(f"out_{i}.txt")):
        path_of_module_folder = Path(__file__).parent
        path_to_product = path_of_module_folder.joinpath(f"out_{i}.txt")
        path_to_product.write_text("I use running globals. How funny.")
```

If you executed these tasks, pytask would collect three tasks as expected. But, only the
last task for `i = 2` would succeed.

The other tasks would fail because they did not produce `out_0.txt` and `out_1.txt`.

Why did the first two tasks fail?

??? note "Explanation"

````
The problem with this example is the running variable `i` which is a global variable
with changing state.

When pytask imports the task module, it collects all three task functions, each of them
having the correct product assigned.

But, when pytask executes the tasks, the running variable `i` in the function body is 2,
or the last state of the loop.

So, all three tasks create the same file, `out_2.txt`.

The solution is to use the intended channels to pass variables to tasks which are the
`kwargs` argument of `@task` or the default value in the
function signature.

```python
for i in range(3):

    @task(kwargs={"i": i})
    def task_example(i, path: Annotated[Path, Product] = Path(f"out_{i}.txt")):
        ...

    # or

    @task
    def task_example(i=i, path: Annotated[Path, Product] = Path(f"out_{i}.txt")):
        ...
```
````
