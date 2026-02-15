# Complex task repetitions

[Task repetitions](../tutorials/repeating_tasks_with_different_inputs.md) are amazing if
you want to execute lots of tasks while not repeating yourself in code.

But, in any bigger project, repetitions can become hard to maintain because there are
multiple layers or dimensions of repetition.

Here you find some tips on how to set up your project such that adding dimensions and
increasing dimensions becomes much easier.

## Example

You can write multiple loops around a task function where each loop stands for a
different dimension. A dimension might represent different datasets or model
specifications to analyze the datasets like in the following example. The task arguments
are derived from the dimensions.

```python
--8 < --"docs_src/how_to_guides/bp_complex_task_repetitions/example.py"
```

There is nothing wrong with using nested loops for simpler projects. But, often projects
are growing over time and you run into these problems.

- When you add a new task, you need to duplicate the nested loops in another module.
- When you add a dimension, you need to touch multiple files in your project and add
  another loop and level of indentation.

## Solution

The main idea for the solution is quickly explained. We will, first, formalize
dimensions into objects using `typing.NamedTuple` or `dataclasses.dataclass`.

Secondly, we will combine dimensions in multi-dimensional objects such that we only have
to iterate over instances of this object in a single loop. Here and for the lack of a
better name, we will call the object an experiment.

Lastly, we will also use the `pytask.DataCatalog` to not be bothered with defining
paths.

!!! note

```
If you have not learned about the `pytask.DataCatalog` yet, start with the
[tutorial](../tutorials/using_a_data_catalog.md) and continue with the
[how-to guide](the_data_catalog.md).
```

```python
--8 < --"docs_src/how_to_guides/bp_complex_task_repetitions/config.py"
```

There are some things to be said.

- The `.name` attributes on each dimension need to return unique names and to ensure
  that by combining them for the name of the experiment, we get a unique and descriptive
  id.
- Dimensions might need more attributes than just a name, like paths, keys for the data
  catalog, or other arguments for the task.

Next, we will use these newly defined data structures and see how our tasks change when
we use them.

```python
--8 < --"docs_src/how_to_guides/bp_complex_task_repetitions/example_improved.py"
```

As you see, we lost a level of indentation and we moved all the generations of names and
paths to the dimensions and multi-dimensional objects.

Using a `pytask.PythonNode` allows us to hash the model and reexecute the task if we
define other model settings.

## Adding another level

Extending a dimension by another level is usually quickly done. For example, if we have
another model that we want to fit to the data, we extend `MODELS` which will
automatically lead to all downstream tasks being created.

```python
...
MODELS = [Model("ols"), Model("logit"), Model("linear_prob"), Model("new_model")]
...
```

Of course, you might need to alter `task_fit_model` because the task needs to handle the
new model as well as the others. Here is where it pays off if you are using high-level
interfaces in your code that handle all of the models with a simple
`fitted_model = fit_model(data=data, model_name=model_name)` call and also return fitted
models that are similar objects.

## Executing a subset

What if you want to execute a subset of tasks, for example, all tasks related to a model
or a dataset?

When you are using the `.name` attributes of the dimensions and multi-dimensional
objects like in the example above, you ensure that the names of dimensions are included
in all downstream tasks.

Thus, you can simply call pytask with the following expression to execute all tasks
related to the logit model.

```console
pytask -k logit
```

!!! note

```
Expressions and markers for selecting tasks are explained in
[selecting tasks](../tutorials/selecting_tasks.md).
```

## Extending repetitions

Some repeated tasks are costly to run - costly in terms of computing power, memory, or
runtime. If you change a task module, you might accidentally trigger all other tasks in
the module to be rerun. Use the `@pytask.mark.persist` decorator, which is explained in
more detail in this [tutorial](../tutorials/making_tasks_persist.md).
