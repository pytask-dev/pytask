# Structure of task files

This section provides advice on how to structure task files.

## TL;DR

- There might be multiple task functions in a task module, but only if the code is still
  readable and not too complex and if runtime for all tasks is low.

- A task function should be the first function in a task module.

  :::{seealso}
  The only exception might be for {doc}`parametrizations <bp_parametrizations>`.
  :::

- The purpose of the task function is to handle IO operations like loading and saving
  files and calling Python functions on the task's inputs. IO should not be handled in
  any other function.

- Non-task functions in the task module are {term}`private functions <private function>`
  and only used within this task module. The functions should not have side-effects.

- Functions used to accomplish tasks in multiple task modules should have their own
  module.

## Best Practices

### Number of tasks in a module

There are two reasons to split tasks across several modules.

The first reason concerns readability and complexity. Multiple tasks deal with
(slightly) different concepts and, thus, should be split content-wise. Even if tasks
deal with the same concept, they might be very complex on its own and separate modules
help the reader (most likely you or your colleagues) to focus on one thing.

The second reason is about runtime. If a task module is changed, all tasks within the
module are re-run. If the runtime of all tasks in the module is high, you wait longer
for your tasks to finish or until an error occurs which prolongs your feedback loops and
hurts your productivity.

### Structure of the module

For the following example, let us assume that the task module contains one task.

The task function should be the first function in the module. It should have a
descriptive name and a docstring which explains what the task accomplishes.

It should be the only {term}`public function` in the module which means the only
function without a leading underscore. This is a convention to keep {term}`public
functions <public function>` separate from {term}`private functions <private function>`
(with a leading underscore) where the latter must only be used in the same module and
not imported elsewhere.

The body of the task function should contain two things:

1. Any IO operations like reading and writing files which are necessary for this task.

   The reason is that IO operations introduce side-effects since the result of the
   function does not only depend on the function arguments, but also on the IO resource
   (e.g., a file on the disk).

   If we bundle all IO operations in the task functions, all other functions used in
   task remain pure (without side-effects) which makes testing the functions easier.

2. The task function should either call {term}`private functions <private function>`
   defined inside the task module or functions which are shared between tasks and
   defined in a module separated from all tasks.

The rest of the module is made of {term}`private functions <private function>` with a
leading underscore which are used to accomplish this and only this task.

Here is an example of a task module which conforms to all advices.

```python
# Content of task_census_data.py.

import pandas as pd
import pytask

from checks import perform_general_checks_on_data


@pytask.mark.depends_on("raw_census.csv")
@pytask.mark.produces("census.pkl")
def task_prepare_census_data(depends_on, produces):
    """Prepare the census data.

    This task prepares the data in three steps.

    1. Clean the data.
    2. Create new variables.
    3. Perform some checks on the new data.

    """
    df = pd.read_csv(depends_on)

    df = _clean_data(df)

    df = _create_new_variables(df)

    perform_general_checks_on_data(df)

    df.to_pickle(produces)


def _clean_data(df):
    ...


def _create_new_variables(df):
    ...
```

:::{seealso}
The structure of the task module is greatly inspired by John Ousterhout's "A
Philosopy of Software Design" in which he coins the name "deep modules". In short,
deep modules have simple interfaces which are defined by one or a few {term}`public
functions <public function>` (or classes) which provide the functionality. The
complexity is hidden inside the module in {term}`private functions <private
function>` which are called by the {term}`public functions <public function>`.
:::
