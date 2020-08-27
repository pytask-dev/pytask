pytask
======

.. image:: https://anaconda.org/pytask/pytask/badges/version.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://anaconda.org/pytask/pytask/badges/platforms.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://readthedocs.org/projects/pytask-dev/badge/?version=latest
    :target: https://pytask-dev.readthedocs.io/en/latest

.. image:: https://github.com/pytask-dev/pytask/workflows/Continuous%20Integration%20Workflow/badge.svg?branch=main
    :target: https://github.com/pytask-dev/pytask/actions?query=branch%3Amain


.. image:: https://codecov.io/gh/pytask-dev/pytask/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/pytask-dev/pytask

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

----

This is the documentation of pytask. You can install the package from `Anaconda.org
<https://anaconda.org/pytask/pytask>`_ with

.. code-block:: bash

    $ conda config --add channels conda-forge --add channels pytask
    $ conda install pytask

The documentation has currently one of four planned parts.

.. raw:: html

    <div class="row">
        <div class="column">
            <a href="tutorials/index.html" id="index-link">
                <div class="card">
                    <img src="_static/images/light-bulb.svg" class="card-img-top"
                         alt="tutorials-icon" height="52"
                    >
                    <h5>Tutorials</h5>
                    <p>
                        Tutorials help you to get started. If you do not know
                        what a build system or pytask is, start here.
                    </p>
                </div>
            </a>
        </div>
        <div class="column">
            <a href="how_to_guides/index.html" id="index-link">
                <div class="card">
                    <img src="_static/images/book.svg" class="card-img-top"
                         alt="how-to guides icon" height="52"
                    >
                    <h5>How-to Guides</h5>
                    <p>
                        How-to guides are designed to provide detailed
                        instructions for very specific and advanced tasks.
                    </p>
                </div>
            </a>
        </div>
        <div class="column">
            <a href="explanations/index.html" id="index-link">
                <div class="card">
                    <img src="_static/images/books.svg" class="card-img-top"
                         alt="explanations icon" height="52"
                    >
                    <h5>Explanations</h5>
                    <p>
                        Explanations give detailed information to key topics and
                        concepts which underlie the package.
                    </p>
                </div>
            </a>
        </div>
        <div class="column">
            <a href="reference_guides/index.html" id="index-link">
                <div class="card">
                    <img src="_static/images/coding.svg" class="card-img-top"
                         alt="reference guides icon" height="52"
                    >
                    <h5>Reference Guides</h5>
                    <p>
                        Reference Guides explain the implementation and provide an
                        entry-point for developers.
                    </p>
                </div>
             </a>
        </div>
    </div>


.. toctree::
    :hidden:

    tutorials/index
    explanations/index
    how_to_guides/index
    reference_guides/index


.. toctree::
   :maxdepth: 1

   glossary
   changes
   api
