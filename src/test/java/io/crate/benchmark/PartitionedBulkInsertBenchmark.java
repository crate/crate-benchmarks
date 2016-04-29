/*
 * Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.benchmark;


import com.carrotsearch.junitbenchmarks.BenchmarkOptions;
import com.carrotsearch.junitbenchmarks.annotation.AxisRange;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkHistoryChart;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkMethodChart;
import io.crate.TimestampFormat;
import io.crate.action.sql.SQLBulkResponse;
import io.crate.shade.org.elasticsearch.common.unit.TimeValue;
import org.junit.Before;
import org.junit.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.core.Is.is;
import static org.hamcrest.core.IsNull.nullValue;


@AxisRange(min = 0)
@BenchmarkHistoryChart(filePrefix="benchmark-partitioned-bulk-insert-history")
@BenchmarkMethodChart(filePrefix = "benchmark-partitioned-bulk-insert")
public class PartitionedBulkInsertBenchmark extends BenchmarkBase {

    public static final String INDEX_NAME = "motiondata";
    public static final int BENCHMARK_ROUNDS = 3;
    public static final int ROWS = 1000;
    public static final int UNIQUE_PARTITIONS = 100;

    private static final String[] partitions = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    private int partitionIndex = 0;
    private static final long TS = TimestampFormat.parseTimestampString("2015-01-01");
    public static final String SINGLE_INSERT_SQL_STMT = "insert into motiondata (d, device_id, ts, ax) values (?,?,?,?)";

    @Before
    public void prepare() {
        execute("set GLOBAL transient bulk.request_timeout='10m', bulk.partition_creation_timeout='10m'");
    }

    @Override
    protected String tableName() {
        return INDEX_NAME;
    }

    @Override
    protected void createTable() {
        execute("create table motiondata (\n" +
                "  d string,\n" +
                "  device_id string,\n" +
                "  ts timestamp,\n" +
                "  ax double,\n" +
                "  primary key (d, device_id, ts)\n" +
                ")\n" +
                "partitioned by (d)\n" +
                "clustered by (device_id)", new Object[0]);
        ensureGreen();
    }

    private Object[][] getBulkArgs(boolean uniquePartitions, int numRows) {
        Object[][] bulkArgs = new Object[numRows][];
        for (int i = 0; i < numRows; i++) {
            bulkArgs[i] = getRandomObject(uniquePartitions);
        }
        return bulkArgs;
    }

    private Object[] getRandomObject(boolean uniquePartitions) {
        int partitionIdx = partitionIndex++;
        String partitionValue = uniquePartitions ? String.valueOf(partitionIdx) : partitions[(partitionIdx) % partitions.length];
        return new Object[]{
                    partitionValue,
                    randomAsciiOfLength(1),
                    TS + partitionIdx,
                    5.0};
    }

    @Test
    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = 1)
    public void testBulkInsertWithBulkArgs() throws Exception {
        executeBulkInsert(getBulkArgs(false, ROWS));
    }

    @Test
    @BenchmarkOptions(benchmarkRounds = 1, warmupRounds = 1)
    public void testBulkInsertWithUniquePartitions() throws Exception {
        executeBulkInsert(getBulkArgs(true, UNIQUE_PARTITIONS));
    }

    private void executeBulkInsert(Object[][] bulkArgs) {
        long inserted = 0;
        long errors = 0;

        SQLBulkResponse bulkResponse = execute(SINGLE_INSERT_SQL_STMT, bulkArgs, TimeValue.timeValueMinutes(7));
        for (SQLBulkResponse.Result result : bulkResponse.results()) {
            assertThat(result.errorMessage(), is(nullValue()));
            if (result.rowCount() < 0) {
                errors++;
            } else {
                inserted += result.rowCount();
            }
        }
        assertThat(errors, is(0L));
        assertThat(inserted, is((long)bulkArgs.length));
    }
}
