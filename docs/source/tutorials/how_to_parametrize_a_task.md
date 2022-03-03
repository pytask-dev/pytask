# How to parametrize a task

You want to define a task which should be repeated over a range of inputs? Parametrize
your task function!

:::{important}
Before v0.2.0, pytask supported only one approach to parametrizations which is similar
to pytest's using a {func}`@pytask.mark.parametrize <_pytask.parametrize.parametrize>`
decorator. You can find it
{doc}`here <../how_to_guides/how_to_parametrize_a_task_the_pytest_way>`.

Here you find the new and preferred approach.
:::

## An example

We reuse the task from the previous {doc}`tutorial <how_to_write_a_task>` which
generates random data and repeat the same operation over a number of seeds to receive
multiple, reproducible samples.

Apply the {func}`@pytask.mark.task <_pytask.task_utils.task>` decorator, loop over the
function and supply different seeds and output paths as default arguments of the
function.

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

```{image} /_static/images/how-to-parametrize-a-task.png
```

## `depends_on` and `produces`

You can also use decorators to supply values to the function.

To specify a dependency which is the same for all parametrizations, add it with
`@pytask.mark.depends_on`. And add a product with `@pytask.mark.produces`

```python
for i in range(10):

    @pytask.mark.task
    @pytask.mark.depends_on(SRC / "common_dependency.file")
    @pytask.mark.produces(f"data_{i}.pkl")
    def task_create_random_data(produces, seed=i):
        rng = np.random.default_rng(seed)
        ...
```

(how-to-parametrize-a-task-the-id)=

## The id

Every task has a unique id which can be used to {doc}`select it <how_to_select_tasks>`.
The normal id combines the path to the module where the task is defined, a double colon,
and the name of the task function. Here is an example.

```
../task_data_preparation.py::task_create_random_data
```

This behavior would produce duplicate ids for parametrized tasks. By default,
auto-generated ids are used which are explained {ref}`here <auto_generated_ids>`.

More powerful are user-defined ids.

(ids)=

### User-defined ids

The {func}`@pytask.mark.task <_pytask.task_utils.task>` decorator has an `id` keyword
which allows the user to set the a special name for the iteration.

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

Parametrizations are becoming more complex quickly. Often, you need to supply many
arguments and ids to tasks.

To organize your ids and arguments use nested dictionaries where keys are ids and values
are dictionaries mapping from argument names to values.

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

Unpacking all the arguments can become tedious. Use instead the `kwargs` argument of the
{func}`@pytask.mark.task <_pytask.task_utils.task` decorator to pass keyword arguments
to the task.

```python
for id_, kwargs in ID_TO_KWARGS.items():

    @pytask.mark.task(id=id_, kwargs=kwargs)
    def task_create_random_data(seed, produces):
        ...
```

As a last step to organize our code even more, we can write a function which creates
`ID_TO_KWARGS`. You can hide the creation of input and output paths and other arguments
in this function.

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
{doc}`best-practices guide on parametrizations <../how_to_guides/bp_parametrizations>`
goes into even more detail on how to scale parametrizations.
