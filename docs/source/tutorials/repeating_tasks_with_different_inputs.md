# Repeating tasks with different inputs

Do you want to repeat a task over a range of inputs? Loop over your task function!

## An example

We reuse the task from the previous {doc}`tutorial <write_a_task>`, which generates
random data and repeats the same operation over several seeds to receive multiple,
reproducible samples.

Apply the {func}`@pytask.mark.task <pytask.mark.task>` decorator, loop over the function
and supply different seeds and output paths as default arguments of the function.

```python
import numpy as np
import pytask


for i in range(10):

    @pytask.mark.task
    def task_create_random_data(produces=f"data_{i}.pkl", seed=i):
        rng = np.random.default_rng(seed)
        ...
```

Executing pytask gives you this:

```{include} ../_static/md/repeating-tasks.md
```

## `depends_on` and `produces`

You can also use decorators to supply values to the function.

To specify a dependency that is the same for all iterations, add it with
{func}`@pytask.mark.depends_on <pytask.mark.depends_on>`. And add a product with
{func}`@pytask.mark.produces <pytask.mark.produces>`

```python
for i in range(10):

    @pytask.mark.task
    @pytask.mark.depends_on(SRC / "common_dependency.file")
    @pytask.mark.produces(f"data_{i}.pkl")
    def task_create_random_data(produces, seed=i):
        rng = np.random.default_rng(seed)
        ...
```

(how-to-repeat-a-task-with-different-inputs-the-id)=

## The id

Every task has a unique id that can be used to {doc}`select it <selecting_tasks>`. The
standard id combines the path to the module where the task is defined, a double colon,
and the name of the task function. Here is an example.

```
../task_data_preparation.py::task_create_random_data
```

This behavior would produce duplicate ids for parametrized tasks. By default,
auto-generated ids are used.

(auto-generated-ids)=

### Auto-generated ids

pytask construct ids by extending the task name with representations of the values used
for each iteration. Booleans, floats, integers, and strings enter the task id directly.
For example, a task function that receives four arguments, `True`, `1.0`, `2`, and
`"hello"`, one of each dtype, has the following id.

```
task_example.py::task_example[True-1.0-2-hello]
```

Arguments with other dtypes cannot be converted to strings and, thus, are replaced with
a combination of the argument name and the iteration counter.

For example, the following function is parametrized with tuples.

```python
@pytask.mark.parametrize("i", [(0,), (1,)])
def task_example(i):
    pass
```

Since the tuples are not converted to strings, the ids of the two tasks are

```
task_example.py::task_example[i0]
task_example.py::task_example[i1]
```

(ids)=

### User-defined ids

The {func}`@pytask.mark.task <pytask.mark.task>` decorator has an `id` keyword, allowing
the user to set a unique name for the iteration.

```python
for seed, id_ in [(0, "first"), (1, "second")]:

    @pytask.mark.task(id=id_)
    def task_create_random_data(seed=i, produces=f"out_{i}.txt"):
        ...
```

produces these ids

```
task_data_preparation.py::task_create_random_data[first]
task_data_preparation.py::task_create_random_data[second]
```

## Complex example

Parametrizations are becoming more complex quickly. Often, there are many tasks with ids
and arguments.

To organize your ids and arguments, use nested dictionaries where keys are ids and
values are dictionaries mapping from argument names to values.

```python
ID_TO_KWARGS = {
    "first": {
        "seed": 0,
        "produces": "data_0.pkl",
    },
    "second": {
        "seed": 1,
        "produces": "data_1.pkl",
    },
}
```

The parametrization becomes

```python
for id_, kwargs in ID_TO_KWARGS.items():

    @pytask.mark.task(id=id_)
    def task_create_random_data(seed=kwargs["seed"], produces=kwargs["produces"]):
        ...
```

Unpacking all the arguments can become tedious. Instead, use the `kwargs` argument of
the {func}`@pytask.mark.task <pytask.mark.task>` decorator to pass keyword arguments to
the task.

```python
for id_, kwargs in ID_TO_KWARGS.items():

    @pytask.mark.task(id=id_, kwargs=kwargs)
    def task_create_random_data(seed, produces):
        ...
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

    @pytask.mark.task(id=id_, kwargs=kwargs)
    def task_create_random_data(i, produces):
        ...
```

The
{doc}`best-practices guide on parametrizations <../how_to_guides/bp_scalable_repetitions_of_tasks>`
goes into even more detail on how to scale parametrizations.

## A warning on globals

The following example warns against accidentally using running variables in your task
definition.

You won't encounter these problems if you strictly use the below-mentioned interfaces.

Look at this repeated task which runs three times and tries to produce a text file with
some content.

```python
import pytask
from pathlib import Path


for i in range(3):

    @pytask.mark.task
    @pytask.mark.produces(f"out_{i}.txt")
    def task_example():
        path_of_module_folder = Path(__file__).parent
        path_to_product = path_of_module_folder.joinpath(f"out_{i}.txt")
        path_to_product.write_text("I use running globals. How funny.")
```

If you executed these tasks, pytask would collect three tasks as expected. But, only the
last task for `i = 2` would succeed.

The other tasks would fail because they did not produce `out_0.txt` and `out_1.txt`.

Why did the first two tasks fail?

```{dropdown} Explanation

The problem with this example is the running variable `i` which is a global variable
with changing state.

When pytask imports the task module, it collects all three task functions, each of them
having the correct product assigned.

But, when pytask executes the tasks, the running variable `i` in the function body is 2,
or the last state of the loop.

So, all three tasks create the same file, `out_2.txt`.

The solution is to use the intended channels to pass variables to tasks which are the
`kwargs` argument of `@pytask.mark.task <pytask.mark.task>` or the default value in the
function signature.

```python
for i in range(3):

    @pytask.mark.task(kwargs={"i": i})
    @pytask.mark.produces(f"out_{i}.txt")
    def task_example(i):
        ...

    # or

    @pytask.mark.task
    @pytask.mark.produces(f"out_{i}.txt")
    def task_example(i=i):
        ...
```
