Parametrizations
================

This section gives advice on how to use parametrizations.


TL;DR
-----

- For very, very simple parametrizations, use parametrizations similar to pytest.

- For the rest, build the signature, the parametrized arguments and ids with a function.

- Create functions to build intermediate objects like output paths which can be shared
  more easily across tasks than the generated values.


Scalability
-----------

Parametrizations allow to scale tasks from :math:`1` to :math:`N` in a simple way. What
is easily overlooked is that parametrizations usually trigger other parametrizations and
the growth in tasks is more :math:`1` to :math:`N \cdot M \cdot \dots` or :math:`1` to
:math:`N^{M \cdot \dots}`.

To keep the resulting complexity as manageable as possible, this guide lays out a
structure which is simple, modular, and scalable.

As an example, assume we have four datasets with one binary dependent variables and some
independent variables. On each of the data sets, we fit three models, a linear model, a
logistic model, and a decision tree. In total, we have :math:`4 \cdot 3 = 12` tasks.

First, let us take a look at the folder and file structure of such a project.

.. code-block::

    src
    │   config.py
    │
    ├───data
    │       data_0.csv
    │       data_1.csv
    │       data_2.csv
    │       data_3.csv
    │
    ├───data_preparation
    │       data_preparation_config.py
    │       task_prepare_data.py
    │
    └───estimation
            estimation_config.py
            task_estimate_models.py

The folder structure, the general ``config.py`` which holds ``SRC`` and ``BLD`` and the
tasks follow the same structure which is advocated for throughout the tutorials.

What is new are the local configuration files in each of the subfolders of ``src`` which
contain objects which are shared across tasks. For example,
``data_preparation_config.py`` holds the paths to the processed data and the names of
the data sets.

.. code-block:: python

    # Content of data_preparation_config.py

    from src.config import BLD
    from src.config import SRC


    DATA = ["data_0", "data_1", "data_2", "data_3"]


    def path_to_input_data(name):
        return SRC / "data" / f"{name}.csv"


    def path_to_processed_data(name):
        return BLD / "data" / f"processed_{name}.pkl"


In the task file ``task_prepare_data.py``, these objects are used to build the
parametrization.

.. code-block:: python

    # Content of task_prepare_data.py

    import pytask

    from src.data_preparation.data_preparation_config import DATA
    from src.data_preparation.data_preparation_config import path_to_input_data
    from src.data_preparation.data_preparation_config import path_to_processed_data


    def _create_parametrization(data):
        parametrizations = []
        ids = []
        for data_name in data:
            ids.append(data_name)
            depends_on = path_to_input_data(data_name)
            produces = path_to_processed_data(data_name)
            parametrizations.append((depends_on, produces))

        return "depends_on, produces", parametrizations, ids


    _SIGNATURE, _PARAMETRIZATION, _IDS = _create_parametrization(DATA)


    @pytask.mark.parametrize(_SIGNATURE, _PARAMETRIZATION, ids=_IDS)
    def task_prepare_data(depends_on, produces):
        ...

All arguments for the ``parametrize`` decorator are built within a function to keep the
logic in one place and the namespace of the module clean.

Ids are used to make the task :ref:`ids <ids>` more descriptive and to simplify their
selection with :ref:`expressions <expressions>`. Here is an example of the task ids with
an explicit id.

.. code-block::

    # With id
    .../src/data_preparation/task_prepare_data.py::task_prepare_data[data_0]

Next, we move to the estimation to see how we can build another parametrization upon the
previous one.

.. code-block:: python

    # Content of estimation_config.py

    from src.config import BLD
    from src.data_preparation.data_preparation_config import DATA


    _MODELS = ["linear_probability", "logistic_model", "decision_tree"]


    ESTIMATIONS = {
        f"{data_name}_{model_name}": {"model": model_name, "data": data_name}
        for model_name in _MODELS
        for data_name in DATA
    }


    def path_to_estimation_result(name):
        return BLD / "estimation" / f"estimation_{name}.pkl"

In the local configuration, we define ``ESTIMATIONS`` which combines the information on
data and model. The key of the dictionary can be used as a task id whenever the
estimation is involved. This allows to trigger all tasks related to one estimation -
estimation, figures, tables - with one command

.. code-block:: console

    pytask -k linear_probability_data_0

And, here is the task file.

.. code-block:: python

    # Content of task_estimate_models.py

    import pytask

    from src.data_preparation.data_preparation_config import path_to_processed_data
    from src.data_preparation.estimation_config import ESTIMATIONS
    from src.data_preparation.estimation_config import path_to_estimation_result


    def _create_parametrization(estimations):
        parametrizations = []
        ids = []
        for name, config in estimations.items():
            ids.append(name)
            depends_on = path_to_processed_data(config["data"])
            produces = path_to_estimation_result(name)
            parametrizations.append((depends_on, config["model"], produces))

        return "depends_on, model, produces", parametrizations, ids


    _SIGNATURE, _PARAMETRIZATION, _IDS = _create_parametrization(ESTIMATIONS)


    @pytask.mark.parametrize(_SIGNATURE, _PARAMETRIZATION, ids=_IDS)
    def task_estmate_models(depends_on, model, produces):
        if model == "linear_probability":
            ...
        ...

Replicating this pattern across a project allows for a clean way to define
parametrizations.


Extending parametrizations
--------------------------

Some parametrized tasks are extremely expensive to run - be it in terms of computing
power, memory or time. On the other hand, parametrizations are often extended which
could also trigger all parametrizations to be rerun. Thus, use the
``@pytask.mark.persist`` decorator which is explained in more detail in this
:doc:`tutorial <../tutorials/how_to_make_tasks_persist>`.
