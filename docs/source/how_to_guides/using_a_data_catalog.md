# Using a data catalog

A data catalog is an inventory for data in your project. It has two main advantages:

- A data catalog provides an interface to easily access the data.
- A data catalog can take care of saving a task product.

## Using the data catalog

As an example, we build a workflow comprising of two tasks that do the following
actions.

1. Read in data from a text file, `input.txt` and storing it as a pickle file.
1. Read the data from pickle, adding additional text and storing it as a text file under
   `output.txt`.

At first, we build the data catalog by registering the data that we provide or that we
later want to access.

```python
from pathlib import Path

from pytask import DataCatalog
from pytask import PathNode


# Get the path of the parent directory of the file.
ROOT = Path(__file__).parent.resolve()


# We store the data in .pytask/
OurDataCatalog = DataCatalog(directory=ROOT / ".pytask")

# Register the input and the output data.
OurDataCatalog.add("input", ROOT / "input.txt")
OurDataCatalog.add("output", ROOT / "output.txt")
```

We also have to create `input.txt` and add some content like `Hello, `.

We do not register the intermediate pickle file, yet.

Next, let us define the two tasks.

```python
def task_save_text_with_pickle(
    path: Annotated[Path, OurDataCatalog["input"]]
) -> Annotated[str, OurDataCatalog["pickle_file"]]:
    text = path.read_text()
    return text


def task_add_content_and_save_text(
    text: Annotated[str, OurDataCatalog["pickle_file"]]
) -> Annotated[str, OurDataCatalog["output"]]:
    text += "World!"
    return text
```

The important bit here is that we reference the intermediate pickle file with
`OurDataCatalog["pickle_file"]`. Since the entry does not exist, the catalog creates a
{class}`~pytask.PickleNode` for this entry and saves the pickle file in the directory
given to the {class}`~pytask.DataCatalog`.

## Changing the default node
