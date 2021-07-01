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

Parametrizations allow to scale tasks from 1 to :math:`N` in a simple way. What is
easily overlooked is that parametrizations usually trigger other parametrizations and
the growth in tasks is more 1 to :math:`N * M` or 1 to :math:`N^M`.

To keep the resulting complexity as manageable as possible, this guide lays out a
structure which is simple, modular, and scalable.

As an example, assume we have four datasets with one binary dependent variables and some
independent variables. On each of the data sets, we fit three models, a linear model, a
logistic model, and a decision tree. Finally, we visualize the performance of the models
with ROC-AUC and Precision-Recall curves. We have :math:`4 * 3 * 2 = 12` tasks in total.

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
    ├───estimation
    │       estimation_config.py
    │       task_estimate_models.py
    │
    └───plotting
            plotting_config.py
            task_plot_metrics.py

The folder structure, the general ``config.py`` which holds ``SRC`` and ``BLD`` and the
tasks follow the same structure which is advocated for throughout the tutorials.

What is new are the local configuration files in each of the subfolders of ``src`` which
are now explained.



First, we define the core of the parametrization which is the Cartesian product of means
and standard deviations.

.. code-block:: python

   import pytask


   MEANS = [0, 1]
   STANDARD_DEVIATIONS = [1, 2]

   CARTESIAN_PRODUCT = itertools.product(MEANS, STANDARD_DEVIATIONS)

Secondly, we need a path where the simulated data is stored. We define it as a function
on the values of the Cartesian product.

.. code-block:: python

   def _create_path_to_simulated_data(mean, standard_devation):
       return f"simulated_data_mean_{mean}_std_{standard_deviation}.pkl"

Thirdly, the complete task for the simulation is

.. code-block:: python

   import numpy as np


   N_SAMPLES = 100_000


   @pytask.mark.parametrize(
       "mean, standard_deviation, produces",
       [
           (mean, std, _create_path_to_simulated_data(mean, std))
           for mean, std in CARTESIAN_PRODUCT
       ],
   )
   def task_simulate_data(mean, standard_deviation, produces):
       data = np.random.normal(mean, standard_deviation, size=N_SAMPLES)
       np.save(produces, data)

Fourthly, we define the task to plot the distribution of the data. First, the function
for the path and, secondly, the task.

.. code-block:: python

   import matplotlib.pyplot as plt


   def _create_path_to_distribution_plot(mean, std):
       f"distribution_plot_mean_{mean}_standard_deviation_{std}.png"


   @pytask.mark.parametrize(
       "depends_on, produces",
       [
           (
               _create_path_to_simulated_data(mean, std),
               _create_path_to_distribution_plot(mean, std),
           )
           for mean, std in CARTESIAN_PRODUCT
       ],
   )
   def task_plot_distribution(depends_on, produces):
       data = np.load(depends_on)

       fig, ax = plt.subplots()
       ax.hist(data)

       plt.savefig(produces)
