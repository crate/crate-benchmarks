==========
Benchmarks
==========

This is a collection of ``spec`` and ``track`` files for use with `cr8
<https://github.com/mfussenegger/cr8>`_.

Please refer to the cr8 readme for more detailed usage information.

Usage
=====

To install it execute::

    $ python3.6 -m venv venv
    $ venv/bin/python -m pip install -r requirements.txt

To run all benchmarks::

    $ venv/bin/cr8 run-track tracks/latest.toml [ -r result-host ]


Visualization & analysis
========================

To visualize and analyze the results use a jupyter notebook::

    $ jupyter notebook

Examples are in the ``notebooks`` folder.


Scripts
=======

This folder contains additional scripts to simplify common tasks:

compare.py
----------

Can be used to quickly launch two different versions and run a spec against
both to compare them.

find_regressions.py
--------------------

Script that will read benchmark results from a table and compare them, printing
out significant regressions.
