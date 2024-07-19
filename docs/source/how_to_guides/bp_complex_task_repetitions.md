# Complex task repetitions

{doc}`Task repetitions <../tutorials/repeating_tasks_with_different_inputs>` are amazing
if you want to execute lots of tasks while not repeating yourself in code.

But, in any bigger project, repetitions can become hard to maintain because there are
multiple layers or dimensions of repetition.

Here you find some tips on how to set up your project such that adding dimensions and
increasing dimensions becomes much easier.

## Example

You can write multiple loops around a task function where each loop stands for a
different dimension. A dimension might represent different datasets or model
specifications to analyze the datasets like in the following example. The task arguments
are derived from the dimensions.

```{literalinclude} ../../../docs_src/how_to_guides/bp_complex_task_repetitions/example.py
---
caption: task_example.py
---
```

There is nothing wrong with using nested loops for simpler projects. But, often projects
are growing over time and you run into these problems.

- When you add a new task, you need to duplicate the nested loops in another module.
- When you add a dimension, you need to touch multiple files in your project and add
  another loop and level of indentation.

## Solution

The main idea for the solution is quickly explained. We will, first, formalize
dimensions into objects and, secondly, combine them in one object such that we only have
to iterate over instances of this object in a single loop.

We will start by defining the dimensions using {class}`~typing.NamedTuple` or
{func}`~dataclasses.dataclass`.

Then, we will define the object that holds both pieces of information together and for
the lack of a better name, we will call it an experiment.

```{literalinclude} ../../../docs_src/how_to_guides/bp_complex_task_repetitions/experiment.py
---
caption: config.py
---
```

There are some things to be said.

- The names on each dimension need to be unique and ensure that by combining them for
  the name of the experiment, we get a unique and descriptive id.
- Dimensions might need more attributes than just a name, like paths, or other arguments
  for the task. Add them.

Next, we will use these newly defined data structures and see how our tasks change when
we use them.

```{literalinclude} ../../../docs_src/how_to_guides/bp_complex_task_repetitions/example_improved.py
---
caption: task_example.py
---
```

As you see, we replaced

## Using the `DataCatalog`

## Adding another dimension

## Adding another level

## Executing a subset

## Grouping and aggregating

## Extending repetitions

Some parametrized tasks are costly to run - costly in terms of computing power, memory,
or time. Users often extend repetitions triggering all repetitions to be rerun. Thus,
use the {func}`@pytask.mark.persist <pytask.mark.persist>` decorator, which is explained
in more detail in this {doc}`tutorial <../tutorials/making_tasks_persist>`.
