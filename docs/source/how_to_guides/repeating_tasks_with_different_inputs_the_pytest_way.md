# Repeating tasks with different inputs - The pytest way

You want to define a task which should be repeated over a range of inputs? Loop over
your task function!

:::{hint}
The process of repeating a function with different inputs is called parametrizations.
:::

:::{important}
This guide shows you how to parametrize tasks with the pytest approach. For the new and
preferred approach, see this
{doc}`tutorial <../tutorials/repeating_tasks_with_different_inputs>`.
:::

You want to define a task which should be repeated over a range of inputs? Parametrize
your task function!

:::{seealso}
If you want to know more about best practices for parametrizations, check out this
{doc}`guide <../how_to_guides/bp_scalable_repititions_of_tasks>` after you made yourself
familiar this tutorial.
:::

## An example

We reuse the previous example of a task which generates random data and repeat the same
operation over a number of seeds to receive multiple, reproducible samples.

First, we write the task for one seed.

```python
import numpy as np
import pytask


@pytask.mark.produces(BLD / "data_0.pkl")
def task_create_random_data(produces):
    rng = np.random.default_rng(0)
    ...
```

In the next step, we repeat the same task over the numbers 0, 1, and 2 and pass them to
the `seed` argument. We also vary the name of the produced file in every iteration.

```python
@pytask.mark.parametrize(
    "produces, seed",
    [(BLD / "data_0.pkl", 0), (BLD / "data_1.pkl", 1), (BLD / "data_2.pkl", 2)],
)
def task_create_random_data(seed, produces):
    rng = np.random.default_rng(seed)
    ...
```

The parametrize decorator receives two arguments. The first argument is
`"produces, seed"` - the signature. It is a comma-separated string where each value
specifies the name of a task function argument.

:::{seealso}
The signature is explained in detail {ref}`below <parametrize-signature>`.
:::

The second argument of the parametrize decorator is a list (or any iterable) which has
as many elements as there are iterations over the task function. Each element has to
provide one value for each argument name in the signature - two in this case.

Putting all together, the task is executed three times and each run the path from the
list is mapped to the argument `produces` and `seed` receives the seed.

:::{note}
If you use `produces` or `depends_on` in the signature of the parametrize decorator, the
values are handled as if they were attached to the function with
{func}`@pytask.mark.depends_on <pytask.mark.depends_on>` or
{func}`@pytask.mark.produces <pytask.mark.produces>`.
:::

## Un-parametrized dependencies

To specify a dependency which is the same for all parametrizations, add it with
{func}`@pytask.mark.depends_on <pytask.mark.depends_on>`.

```python
@pytask.mark.depends_on(SRC / "common_dependency.file")
@pytask.mark.parametrize(
    "produces, seed",
    [(BLD / "data_0.pkl", 0), (BLD / "data_1.pkl", 1), (BLD / "data_2.pkl", 2)],
)
def task_create_random_data(seed, produces):
    rng = np.random.default_rng(seed)
    ...
```

(parametrize-signature)=

## The signature

The signature can be passed in three different formats.

1. The signature can be a comma-separated string like an entry in a csv table. Note that
   white-space is stripped from each name which you can use to separate the names for
   readability. Here are some examples:

   ```python
   "single_argument"
   "first_argument,second_argument"
   "first_argument, second_argument"
   ```

1. The signature can be a tuple of strings where each string is one argument name. Here
   is an example.

   ```python
   ("first_argument", "second_argument")
   ```

1. Finally, it is also possible to use a list of strings.

   ```python
   ["first_argument", "second_argument"]
   ```

## The id

Every task has a unique id which can be used to
{doc}`select it <../tutorials/selecting_tasks>`. The normal id combines the path to
the module where the task is defined, a double colon, and the name of the task function.
Here is an example.

```
../task_example.py::task_example
```

This behavior would produce duplicate ids for parametrized tasks. Therefore, there exist
multiple mechanisms to produce unique ids.

(auto-generated-ids)=

### Auto-generated ids

To avoid duplicate task ids, the ids of parametrized tasks are extended with
descriptions of the values they are parametrized with. Booleans, floats, integers and
strings enter the task id directly. For example, a task function which receives four
arguments, `True`, `1.0`, `2`, and `"hello"`, one of each dtype, has the following id.

```
task_example.py::task_example[True-1.0-2-hello]
```

Arguments with other dtypes cannot be easily converted to strings and, thus, are
replaced with a combination of the argument name and the iteration counter.

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

### User-defined ids

Instead of a function, you can also pass a list or another iterable of id values via
`ids`.

This code

```python
@pytask.mark.parametrize("i", [(0,), (1,)], ids=["first", "second"])
def task_example(i):
    pass
```

produces these ids

```
task_example.py::task_example[first]  # (0,)
task_example.py::task_example[second]  # (1,)
```

(how-to-parametrize-a-task-convert-other-objects)=

### Convert other objects

To change the representation of tuples and other objects, you can pass a function to the
`ids` argument of the {func}`@pytask.mark.parametrize <pytask.mark.parametrize>`
decorator. The function is called for every argument and may return a boolean, number,
or string which will be integrated into the id. For every other return, the
auto-generated value is used.

To get a unique representation of a tuple, we can use the hash value.

```python
def tuple_to_hash(value):
    if isinstance(value, tuple):
        return hash(a)


@pytask.mark.parametrize("i", [(0,), (1,)], ids=tuple_to_hash)
def task_example(i):
    pass
```

This produces the following ids:

```
task_example.py::task_example[3430018387555]  # (0,)
task_example.py::task_example[3430019387558]  # (1,)
```
