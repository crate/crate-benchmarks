/*
 * Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
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
import com.carrotsearch.junitbenchmarks.annotation.LabelType;
import io.crate.testserver.action.sql.SQLResponse;
import io.crate.testserver.shade.org.elasticsearch.action.update.UpdateAction;
import io.crate.testserver.shade.org.elasticsearch.action.update.UpdateRequest;
import io.crate.testserver.shade.org.elasticsearch.action.update.UpdateResponse;
import org.junit.Before;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;

@AxisRange(min = 0)
@BenchmarkHistoryChart(filePrefix="benchmark-update-history", labelWith = LabelType.CUSTOM_KEY)
@BenchmarkMethodChart(filePrefix = "benchmark-update")
public class UpdateBenchmark extends BenchmarkBase {

    public static final int NUM_REQUESTS_PER_TEST = 100;
    public static final int BENCHMARK_ROUNDS = 100;

    public String updateId = null;

    @Override
    public boolean importData() {
        return true;
    }

    @Before
    public void getUpdateIds() {
        if (updateId == null) {
            SQLResponse response = execute("SELECT \"_id\" FROM countries WHERE \"countryCode\"=?", new Object[]{"AT"});
            assert response.rows().length == 1;
            updateId = (String)response.rows()[0][0];
        }
    }

    public UpdateRequest getApiUpdateByIdRequest() {
        Map<String, Integer> updateDoc = new HashMap<>();
        updateDoc.put("population", Math.abs(getRandom().nextInt()));
        return new UpdateRequest(TABLE_NAME, "default", updateId).doc(updateDoc);
    }

    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = 1)
    @Test
    public void testUpdateSql() {
        for (int i=0; i<NUM_REQUESTS_PER_TEST; i++) {
            SQLResponse response = execute(
                    "UPDATE countries SET population=? WHERE \"countryCode\"=?",
                    new Object[]{ Math.abs(getRandom().nextInt()), "US" });
            assertEquals(
                    1,
                    response.rowCount()
            );
        }
    }


    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = 1)
    @Test
    public void testUpdateSqlById() {
        for (int i=0; i<NUM_REQUESTS_PER_TEST; i++) {
            SQLResponse response = execute(
                    "UPDATE countries SET population=? WHERE \"_id\"=?",
                    new Object[]{ Math.abs(getRandom().nextInt()), updateId }
            );
            assertEquals(
                    1,
                    response.rowCount()
            );
        }
    }

    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = 1)
    @Test
    public void testUpdateApiById() {
        for (int i=0; i<NUM_REQUESTS_PER_TEST; i++) {
            UpdateResponse response = esClient.execute(UpdateAction.INSTANCE, getApiUpdateByIdRequest()).actionGet();
            assertEquals(updateId, response.getId());
        }
    }
}
