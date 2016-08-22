===================
Crate Benchmark API
===================

Installation
============

The `Flask`_ application is bootstrapped using buildout::

  python3.4 bootstrap.py
  bin/buildout -N

Then run the application using the ``bin/app`` command::

  bin/crate --help
  usage: app [-h] [--http-port HTTP_PORT] [--http-host HTTP_HOST]
             [--crate-hosts CRATE_HOSTS] [--debug]

  optional arguments:
    -h, --help            show this help message and exit
    --http-port HTTP_PORT
                          HTTP port
    --http-host HTTP_HOST
                          HTTP host
    --crate-hosts CRATE_HOSTS
                          Crate hosts
    --debug               Start HTTP server in debug mode


Usage
=====

REST Endpoint::

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
