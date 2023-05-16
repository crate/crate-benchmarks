====================
Join Order Benchmark
====================

Join order benchmarks based on:

https://github.com/gregrahn/join-order-benchmark


Setup
=====

- Download the data::

    wget http://homepages.cwi.nl/~boncz/job/imdb.tgz

- Extract it::

    aunpack imdb.tgz

The files should go into a ``imdb`` folder relative to the
``join-order-benchmark`` folder containing *this* README.


- Create and activate a Python virtualenv for the requirements.txt in the
  repository root.


Usage
=====

::

    cr8 run-spec job.toml localhost:4200
