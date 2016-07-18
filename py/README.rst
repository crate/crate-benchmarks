==========
Benchmarks
==========

This is a collection of ``spec`` and ``track`` files for use with `cr8
<https://github.com/mfussenegger/cr8>`_.

Please refer to the cr8 readme for more detailed usage information.

Usage
=====

To install it execute::

    $ python3.5 -m venv venv
    $ venv/bin/python -m pip install -r requirements.txt

If you want to visualize and analyze the results execute::

    $ venv/bin/python -m pip install -r requirements-viz.txt

To run all benchmarks::

    $ venv/bin/cr8 run-track tracks/latest.toml [ -r result-host ]

To visualize and analyze the results use a jupyter notebook::

    $ jupyter notebook

Examples are in the ``notebooks`` folder.
