=================
Python Benchmarks
=================

A collection of ``spec`` and ``track`` files for use with cr8_.

Usage
=====

To install, run::

    $ python3.6 -m venv venv
    $ venv/bin/python -m pip install -r requirements.txt

To run all benchmarks, do::

    $ venv/bin/cr8 run-track tracks/latest.toml [ -r result-host ]

Visualization and Analysis
==========================

To visualize and analyze the results, use a jupyter_ notebook::

    $ jupyter notebook

Examples are in the notebooks_ folder.

Scripts
=======

Scripts to simply common tasks:

- compare.py_: compare a spec against two different versions of CrateDB.

- find_regressions.py_: read benchmark results from a table and compare them for
  regressions.


Writing Benchmarks
==================

Since executing the benchmarks can take up quite some time we value quality
over quantity here.

Benchmarks should be written so that they represent common execution paths or
common use cases that differ a lot from other cases.

When writing new benchmarks it's also advisable to run `compare.py` once, where
``--v1 == --v2`` to get a feeling of the stability of the benchmark. If there
is a large difference, the benchmark should be tuned as it would be too
unreliable to spot real differences.


.. _compare.py: compare.py
.. _cr8: https://github.com/mfussenegger/cr8
.. _find_regressions.py: find_regressions.py
.. _jupyter: https://jupyter.org/
.. _notebooks: notebooks
