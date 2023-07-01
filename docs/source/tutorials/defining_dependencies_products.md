# Defining dependencies and products

To ensure pytask executes all tasks in the correct order, define which dependencies are
required and which products are produced by a task.

:::{important}
If you do not specify dependencies and products as explained below, pytask will not be
able to build a graph, a {term}`DAG`, and will not be able to execute all tasks in the
project correctly!
:::

## Products

Let's revisit the task from the {doc}`previous tutorial <write_a_task>`.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```python
from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = BLD / "data.pkl"
) -> None:
    ...
```

Using {class}`~pytask.Product` allows to declare an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} Python 3.7+
:sync: python37plus

```python
from pathlib import Path

from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = BLD / "data.pkl"
) -> None:
    ...
```

Using {class}`~pytask.Product` allows to declare an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} Decorators (deprecated)
:sync: decorators

```python
from pathlib import Path

from my_project.config import BLD


@pytask.mark.produces(BLD / "data.pkl")
def task_create_random_data(produces: Path) -> None:
    ...
```

The {func}`@pytask.mark.produces <pytask.mark.produces>` marker attaches a
product to a task which is a {class}`pathlib.Path` to file. After the task has finished,
pytask will check whether the file exists.

Optionally, you can use `produces` as an argument of the task function and get access to
the same path inside the task function.

:::
::::

:::{tip}
If you do not know about {mod}`pathlib` check out [^id3] and [^id4]. The module is
beneficial for handling paths conveniently and across platforms.
:::

## Dependencies

Most tasks have dependencies. Here, you see how you can declare dependencies for a task
so that pytask can make sure the dependencies are present or created before the task is
executed.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus


```python
from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl",
    path_to_plot: Annotated[Path, Product] = BLD / "plot.png"
) -> None:
    df = pd.read_pickle(path_to_data)
    ...
```
:::

:::{tab-item} Python 3.7+
:sync: python37plus


```python
from pathlib import Path

from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl",
    path_to_plot: Annotated[Path, Product] = BLD / "plot.png"
) -> None:
    df = pd.read_pickle(path_to_data)
    ...
```
:::

:::{tab-item} Decorators (deprecated)
:sync: decorators

```python
from pathlib import Path

from my_project.config import BLD


@pytask.mark.depends_on(BLD / "data.pkl")
@pytask.mark.produces(BLD / "plot.png")
def task_plot_data(depends_on: Path, produces: Path) -> None:
    df = pd.read_pickle(depends_on)
    ...
```

Use `depends_on` as a function argument to access the dependency path inside the
function and load the data.

:::
::::

## Relative paths

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

You can also use absolute and relative paths as strings that obey the same rules as the
{class}`pathlib.Path`.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```python
from pathlib import Path
from typing import Annotated

from pytask import Product


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = Path("../bld/data.pkl")
) -> None:
    ...
```
:::

:::{tab-item} Python 3.7+
:sync: python37plus

```python
from pathlib import Path

from pytask import Product
from typing_extensions import Annotated


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = Path("../bld/data.pkl")
) -> None:
    ...
```
:::

:::{tab-item} Decorators (deprecated)
:sync: decorators

```python
from pathlib import Path


@pytask.mark.produces("../bld/data.pkl")
def task_create_random_data(produces: Path) -> None:
    ...
```

If you use `depends_on` or `produces` as arguments for the task function, you will have
access to the paths of the targets as {class}`pathlib.Path`.

:::
::::

## Multiple dependencies and products

Tasks can have multiple dependencies and products.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```python
from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


def task_plot_data(
    path_to_data_0: Path = BLD / "data_0.pkl",
    path_to_data_1: Path = BLD / "data_1.pkl",
    path_to_plot_0: Annotated[Path, Product] = BLD / "plot_0.png",
    path_to_plot_1: Annotated[Path, Product] = BLD / "plot_1.png",
) -> None:
    ...
```

You can group your dependencies and product if you prefer not having a function argument
per input. Use dictionaries (recommended), tuples, lists, or more nested structures if
you need.

```python
from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


_DEPENDENCIES = {"data_0": BLD / "data_0.pkl", "data_1": BLD / "data_1.pkl"}
_PRODUCTS = {"plot_0": BLD / "plot_0.png", "plot_1": BLD / "plot_1.png"}

def task_plot_data(
    path_to_data: dict[str, Path] = _DEPENDENCIES,
    path_to_plots: Annotated[dict[str, Path], Product] = _PRODUCTS,
) -> None:
    ...
```

:::

:::{tab-item} Python 3.7+
:sync: python37plus

```python
from pathlib import Path

from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


def task_plot_data(
    path_to_data_0: Path = BLD / "data_0.pkl",
    path_to_data_1: Path = BLD / "data_1.pkl",
    path_to_plot_0: Annotated[Path, Product] = BLD / "plot_0.png",
    path_to_plot_1: Annotated[Path, Product] = BLD / "plot_1.png",
) -> None:
    ...
```

You can group your dependencies and product if you prefer not having a function argument
per input. Use dictionaries (recommended), tuples, lists, or more nested structures if
you need.

```python
from pathlib import Path
from typing import Dict

from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


_DEPENDENCIES = {"data_0": BLD / "data_0.pkl", "data_1": BLD / "data_1.pkl"}
_PRODUCTS = {"plot_0": BLD / "plot_0.png", "plot_1": BLD / "plot_1.png"}

def task_plot_data(
    path_to_data: Dict[str, Path] = _DEPENDENCIES,
    path_to_plots: Annotated[Dict[str, Path], Product] = _PRODUCTS,
) -> None:
    ...
```

:::

:::{tab-item} Decorators (deprecated)
:sync: decorators

The easiest way to attach multiple dependencies or products to a task is to pass a
{class}`dict` (highly recommended), {class}`list`, or another iterator to the marker
containing the paths.

To assign labels to dependencies or products, pass a dictionary. For example,

```python
from typing import Dict


@pytask.mark.produces({"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"})
def task_create_random_data(produces: Dict[str, Path]) -> None:
    ...
```

Then, use `produces` inside the task function.

```pycon
>>> produces["first"]
BLD / "data_0.pkl"

>>> produces["second"]
BLD / "data_1.pkl"
```

You can also use lists and other iterables.

```python
@pytask.mark.produces([BLD / "data_0.pkl", BLD / "data_1.pkl"])
def task_create_random_data(produces):
    ...
```

Inside the function, the arguments `depends_on` or `produces` become a dictionary where
keys are the positions in the list.

```pycon
>>> produces
{0: BLD / "data_0.pkl", 1: BLD / "data_1.pkl"}
```

Why does pytask recommend dictionaries and convert lists, tuples, or other
iterators to dictionaries? First, dictionaries with positions as keys behave very
similarly to lists.

Secondly, dictionaries use keys instead of positions that are more verbose and
descriptive and do not assume a fixed ordering. Both attributes are especially desirable
in complex projects.

## Multiple decorators

pytask merges multiple decorators of one kind into a single dictionary. This might help
you to group dependencies and apply them to multiple tasks.

```python
common_dependencies = pytask.mark.depends_on(
    {"first_text": "text_1.txt", "second_text": "text_2.txt"}
)


@common_dependencies
@pytask.mark.depends_on("text_3.txt")
def task_example(depends_on):
    ...
```

Inside the task, `depends_on` will be

```pycon
>>> depends_on
{"first_text": ... / "text_1.txt", "second_text": "text_2.txt", 0: "text_3.txt"}
```

## Nested dependencies and products

Dependencies and products can be nested containers consisting of tuples, lists, and
dictionaries. It is beneficial if you want more structure and nesting.

Here is an example of a task that fits some model on data. It depends on a module
containing the code for the model, which is not actively used but ensures that the task
is rerun when the model is changed. And it depends on the data.

```python
@pytask.mark.depends_on(
    {
        "model": [SRC / "models" / "model.py"],
        "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
    }
)
@pytask.mark.produces(BLD / "models" / "fitted_model.pkl")
def task_fit_model(depends_on, produces):
    ...
```

`depends_on` within the function will be

```python
{
    "model": [SRC / "models" / "model.py"],
    "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
}
```

:::
::::


## References

[^id3]: The official documentation for {mod}`pathlib`.

[^id4]: A guide for pathlib by [realpython](https://realpython.com/python-pathlib/).
