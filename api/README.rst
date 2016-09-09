===================
Crate Benchmark API
===================

Installation
============

The `Flask`_ application is bootstrapped using virtualenv::

  python3.4 -m venv env
  source env/bin/activate
  pip install --upgrade pip
  pip install -e .

Usage
=====

There are 2 commands: ``server`` and ``add-timestamp``::

  > bench-api --help
  usage: bench-api [-h] --conf CONF {server,add-timestamp} ...

  positional arguments:
    {server,add-timestamp}

  optional arguments:
    -h, --help            show this help message and exit
    --conf CONF           Path to config.tomUsage

server
------

Run API that reads benchmark result data from Crate cluster::

  > bench-api --conf config.toml server

For help::

  > bench-api server --help


add-timestamp
-------------

Resolve timestamp of Github commit hash and store it in doc.benchmarks table::

  > bench-api --conf config.toml add-timestamp

For help::

  > bench-api add-timestamp --help

REST Endpoint
=============

::

  -> GET /result/<benchmark-group>?[&from=<isotime>&to=<isotime>]
  [{...}, {...}, ...] # Crate data format

The API call will result in this query:

.. code-block:: sql

  SELECT ? as "group",
    version_info['number'] as "version",
    version_info['timestamp'] as "version",
    runtime_stats['min'] as "min",
    runtime_stats['median'] as "median",
    runtime_stats['max'] as "max",
    runtime_stats['stdev'] as "stdev",
    runtime_stats['variance'] as "variance",
    statement
  FROM "benchmark"."history"
  WHERE statement = ANY(?)
    AND version_info['build_timestamp'] >= ?
    AND version_info['build_timestamp'] <= ?
  ORDER BY version, statement

Table Schema
============

The table schema is defined by the `cr8`_ tool.

.. code-block:: sql

  CREATE TABLE IF NOT EXISTS "benchmark"."history" (
      version_info OBJECT (STRICT) AS (
          number STRING,
          hash STRING
      ),
      statement STRING,
      started TIMESTAMP,
      ended TIMESTAMP,
      concurrency INTEGER,
      bulk_size INTEGER,
      runtime_stats OBJECT (STRICT) AS (
          avg DOUBLE,
          min DOUBLE,
          max DOUBLE,
          mean DOUBLE,
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
          hist ARRAY(OBJECT (STRICT) AS (
              bin DOUBLE,
              num INTEGER
          ))
      )
  ) CLUSTERED INTO 8 SHARDS WITH (
      number_of_replicas = '1-3',
      column_policy = 'strict'
  )

.. _Flask: http://flask.pocoo.org
