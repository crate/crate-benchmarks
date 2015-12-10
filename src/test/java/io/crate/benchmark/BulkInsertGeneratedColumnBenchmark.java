/*
 * Licensed to Crate under one or more contributor license agreements.
 * See the NOTICE file distributed with this work for additional
 * information regarding copyright ownership.  Crate licenses this file
 * to you under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 * implied.  See the License for the specific language governing
 * permissions and limitations under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial
 * agreement.
 */

package io.crate.benchmark;


import com.carrotsearch.junitbenchmarks.BenchmarkOptions;
import com.carrotsearch.junitbenchmarks.annotation.AxisRange;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkHistoryChart;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkMethodChart;
import com.carrotsearch.junitbenchmarks.annotation.LabelType;
import io.crate.testserver.action.sql.SQLBulkResponse;
import org.junit.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.core.Is.is;

@AxisRange(min = 0)
@BenchmarkHistoryChart(filePrefix="benchmark-bulk-insert-t175-history", labelWith = LabelType.CUSTOM_KEY)
@BenchmarkMethodChart(filePrefix = "benchmark-bulk-insert-t175")
public class BulkInsertGeneratedColumnBenchmark extends BenchmarkBase {

    public static final int BENCHMARK_ROUNDS = 10;

    @Override
    protected void createTable() {
        execute("create table \"" + TABLE_NAME + "\" (" +
                " \"areaInSqKm\" float," +
                " capital string," +
                " continent string," +
                " \"continentName\" string," +
                " \"countryCode\" string," +
                " \"countryName\" string," +
                " \"currencyCode\" string," +
                " east float," +
                " \"fipsCode\" string," +
                " \"isoAlpha3\" string," +
                " \"isoNumeric\" string," +
                " languages string," +
                " north float," +
                " population integer," +
                " population_generated integer GENERATED ALWAYS AS (population + 1)," +
                " south float," +
                " west float" +
                ") clustered into 2 shards with (number_of_replicas=0)", new Object[0]);
        testCluster.ensureGreen();
    }

    @Test
    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = 1)
    public void testBulkInsertWithGeneratedColumn() throws Exception {
        SQLBulkResponse bulkResponse = execute(BulkInsertBenchmark.BULK_INSERT_SQL_STMT, BulkInsertBenchmark.getBulkArgs());
        assertThat(bulkResponse.results().length, is(BulkInsertBenchmark.ROWS));
    }

}
