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
) CLUSTERED INTO 6 SHARDS WITH (
    number_of_replicas = '0-2',
    column_policy = 'strict'
);
