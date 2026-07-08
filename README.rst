==================
CrateDB Benchmarks
==================

A collection of CrateDB_ benchmarks based on ``spec`` and ``track`` files for
use with cr8_.

Benchmark results are used to compare performance between two different CrateDB
versions.

.. note::

   Some benchmarks are not covering every single case but are more intended to
   be compared against others to see differences when certain features are
   enabled/disabled.

Usage
=====

To install, run::

    $ python3.6 -m venv venv
    $ venv/bin/python -m pip install -r requirements.txt

To run all benchmarks, do::

    $ venv/bin/cr8 run-track tracks/latest.toml [ -r result-host ]

To run a single benchmark (spec)::

    $ venv/bin/cr8 run-spec specs/specfile.toml localhost:4200

For more information on the parameters run::

    $ venv/bin/cr8 run-spec -h

.. note::

   venv_ is a Python module that provides support for creating lightweight
   virtual environments.

.. note::

   Running an individual spec requires that you have a running CrateDB instance
   and that you pass its host:port as the last parameter.


Scripts
=======

Scripts to simplify common tasks:

- compare_measures.py_: compare measures read from two files

- compare_run.py_: compare a spec against two different versions of CrateDB.

- find_regressions.py_: read benchmark results from a table and compare them for
  regressions.

Writing Benchmarks
==================

Since executing the benchmarks can take up quite some time we value quality
over quantity here.

Benchmarks should be written so that they represent common execution paths or
common use cases that differ a lot from other cases.

When writing new benchmarks it's also advisable to run ``compare_run.py`` once,
where ``--v1 == --v2`` to get a feeling of the stability of the benchmark. If
there is a large difference, the benchmark should be tuned as it would be too
unreliable to spot real differences.

Troubleshooting
===============

perf metrics are missing
------------------------

``compare_run.py`` uses ``perf stat`` to collect hardware counters from the
CrateDB process. If the run prints messages like::

    perf: skipping non-JSON line: 'Access to performance monitoring and observability operations is limited.'

then access to perf events is restricted by the ``kernel.perf_event_paranoid``
sysctl setting. To allow per-process monitoring::

    $ sudo sysctl kernel.perf_event_paranoid=1

See the kernel documentation on `perf security`_ for the available levels and
how to make the setting permanent. The benchmark itself runs fine without perf
access; only the perf metrics in the comparison output will be empty.

Help
====

Looking for more help?

- Check out our `support channels`_

.. _compare_measures.py: compare_measures.py
.. _compare_run.py: compare_run.py
.. _cr8: https://codeberg.org/mfussenegger/cr8
.. _Crate.io: http://crate.io/
.. _CrateDB: https://github.com/crate/crate
.. _find_regressions.py: find_regressions.py
.. _jupyter: https://jupyter.org/
.. _notebooks: notebooks
.. _perf security: https://www.kernel.org/doc/html/latest/admin-guide/perf-security.html
.. _support channels: https://crate.io/support/
.. _venv: https://docs.python.org/3/library/venv.html
.. _toml: https://learnxinyminutes.com/docs/toml/
