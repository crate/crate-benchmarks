=============
Benchmark API
=============

A Flask_ application that reads CrateDB benchmark results from Microsoft Azure.

Setup
=====

Bootstrap the application like so::

    $ python3.4 -m venv env
    $ source env/bin/activate
    $ pip install --upgrade pip
    $ pip install -e .

Usage
=====

The ``bench-api`` CLI tool has two commands: ``server`` and ``add-timestamp``.

To read data from the CrateDB cluster, use the ``server`` command::

    $ bench-api --conf config.toml server

For help, run::

    $ bench-api server --help

To resolve the timestamp of a GitHub commit hash and store it in
``doc.benchmarks`` table, run::

    $ bench-api --conf config.toml add-timestamp

For help, run::

    $ bench-api add-timestamp --help

REST Endpoint
=============

This app exposes the following REST endpoint:

    /result/<BENCHMARK_GROUP>?[&from=<FROM_ISOTIME>&to=<TO_ISOTIME>]

This results in the following query:

.. code-block:: sql

      SELECT ? as "group",
             meta['name'] as spec_name,
             version_info as version,
             version_info['number'] as build_version,
             version_info['date'] as build_timestamp,
             runtime_stats['min'] as min,
             runtime_stats['median'] as median,
             runtime_stats['max'] as max,
             runtime_stats['stdev'] as stdev,
             runtime_stats['variance'] as variance,
             statement
        FROM doc.benchmarks
       WHERE meta['name'] = ANY(?)
         AND version_info['date'] >= ?
         AND version_info['date'] <= ?
    ORDER BY build_timestamp, build_version, spec_name, statement

Here, ``<BENCHMARK_GROUP>``, ``<FROM_ISOTIME>``, and ``<TO_ISOTIME>`` from the
URL are substituted into the query where the ``?`` characters appear.

Table Schema
============

The ``benchmark.history`` table schema is defined as:

.. code-block:: sql

  CREATE TABLE IF NOT EXISTS "doc"."benchmarks" (
      version_info OBJECT (STRICT) AS (
          number STRING,
          hash STRING,
          date TIMESTAMP
      ),
      statement STRING,
      started TIMESTAMP,
      ended TIMESTAMP,
      concurrency INTEGER,
      bulk_size INTEGER,
      meta OBJECT AS (
        name STRING
      ),
      runtime_stats OBJECT (STRICT) AS (
          avg DOUBLE,
          min DOUBLE,
          max DOUBLE,
          mean DOUBLE,
          error_margin DOUBLE,
          median DOUBLE,
          percentile OBJECT AS (
              "50" DOUBLE,
              "75" DOUBLE,
              "90" DOUBLE,
              "99" DOUBLE,
              "99_9" DOUBLE
          ),
          n INTEGER,
          variance DOUBLE,
          stdev DOUBLE,
          samples ARRAY(DOUBLE)
      )
  ) CLUSTERED INTO 8 SHARDS WITH (
      number_of_replicas = '1-3',
      column_policy = 'strict'
  )


Public Benchmark Service
========================

The public benchmark service runs as a systemd service on
``bench-upstream.srv1.azure.fir.io``.c

You can start the service like so::

    $ sudo systemctl start benchmark-crate-io.service

.. _Flask: http://flask.pocoo.org
