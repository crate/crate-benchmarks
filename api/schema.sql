CREATE TABLE IF NOT EXISTS "benchmark"."history" (
    version_info OBJECT (STRICT) AS (
        number STRING,
        hash STRING,
        timestamp TIMESTAMP
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
);
