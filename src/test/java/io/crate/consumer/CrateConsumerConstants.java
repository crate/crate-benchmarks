package io.crate.consumer;

public class CrateConsumerConstants {

    private static final String TABLE_NAME = "benchmark.history";

    static final String CRATE_HOST = "jub.crate.host";
    static final String CRATE_TRANSPORT_PORT = "jub.crate.transport";

    static final String CREATE_TABLE_IF_NOT_EXISTS_STMT = String.format("CREATE TABLE IF NOT EXISTS %s (" +
            " benchmark_group STRING PRIMARY KEY," +
            " method STRING PRIMARY KEY," +
            " build_timestamp TIMESTAMP PRIMARY KEY," +
            " build_version STRING," +
            " bench_run_timestamp TIMESTAMP," +
            " benchmark_values OBJECT (STRICT) AS (" +
            "   benchmark_rounds LONG," +
            "   benchmark_time_total TIMESTAMP," +
            "   gc_avg DOUBLE," +
            "   gc_invocations LONG," +
            "   gc_stddev DOUBLE," +
            "   gc_time TIMESTAMP," +
            "   round_avg DOUBLE," +
            "   round_stddev DOUBLE," +
            "   warmup_rounds LONG," +
            "   warmup_time_total TIMESTAMP" +
            " )" +
            ") with (number_of_replicas = 2)", TABLE_NAME);

    static final String INSERT_STMT = String.format("INSERT INTO %s" +
            " (benchmark_group, method, build_version, build_timestamp, bench_run_timestamp, benchmark_values)" +
            " VALUES (?, ?, ?, ?, ?, ?)", TABLE_NAME);

    static final String SELECT_VERSIONS = "select version['number'] from sys.nodes";

}
