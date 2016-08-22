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

The API call will result in this query::

  SELECT benchmark_group as "group",
         method,
         build_timestamp as "timestamp",
         build_version as "version",
         benchmark_values['round_avg'] as "avg",
         benchmark_values['round_stddev'] as "stddev"
  FROM benchmark.history
  WHERE benchmark_group = ?
    AND build_timestamp >= ?
    AND build_timestamp <= ?
  ORDER BY build_timestamp, method

Table Schema
============

::

  CREATE TABLE IF NOT EXISTS "benchmark"."history" (
    "bench_run_timestamp" TIMESTAMP,
    "benchmark_group" STRING,
    "benchmark_values" OBJECT (STRICT) AS (
      "benchmark_rounds" LONG,
      "benchmark_time_total" TIMESTAMP,
      "gc_avg" DOUBLE,
      "gc_invocations" LONG,
      "gc_stddev" DOUBLE,
      "gc_time" TIMESTAMP,
      "round_avg" DOUBLE,
      "round_stddev" DOUBLE,
      "warmup_rounds" LONG,
      "warmup_time_total" TIMESTAMP
    ),
    "build_timestamp" TIMESTAMP,
    "build_version" STRING,
    "method" STRING
  )


.. _Flask: http://flask.pocoo.org
