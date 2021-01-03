Parametrizations
================

This section gives advice on how to use parametrizations.


TL;DR
-----

- For very simple parametrizations, use parametrizations like with pytest.

- For more complex cases, build the inputs values for the parametrization with a
  function. The function should be placed at the top of the task module.

- If you are reusing a parametrization or parts of it for multiple tasks, code it as
  modular as possible. Separate the underlying Cartesian product from other values which
  can be computed by functions on the Cartesian product.


Best Practices
--------------

Reusing parametrizations
~~~~~~~~~~~~~~~~~~~~~~~~

In some projects, you might want to reuse parametrizations or slight variations thereof
for multiple tasks.

To make the scenario more concrete, we want to simulate data by parametrizing a task
with the mean and standard deviation of a normal distribution. Then, we want to reuse
the parametrization to plot the simulated distributions.

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
