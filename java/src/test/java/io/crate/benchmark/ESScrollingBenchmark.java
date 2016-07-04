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

import com.carrotsearch.junitbenchmarks.annotation.BenchmarkHistoryChart;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkMethodChart;
import com.carrotsearch.junitbenchmarks.annotation.LabelType;
import io.crate.shade.org.elasticsearch.common.bytes.BytesArray;
import io.crate.shade.org.elasticsearch.common.logging.ESLogger;
import io.crate.shade.org.elasticsearch.common.logging.Loggers;

import java.io.IOException;
import java.util.Random;

@BenchmarkHistoryChart(filePrefix="benchmark-lucenedoccollector-history", labelWith = LabelType.CUSTOM_KEY)
@BenchmarkMethodChart(filePrefix = "benchmark-lucenedoccollector")
public class ESScrollingBenchmark extends BenchmarkBase {

    public static final int BENCHMARK_ROUNDS = 100;
    // should be in-sync with sql->Paging.PAGE_SIZE

    public final static ESLogger logger = Loggers.getLogger(ESScrollingBenchmark.class);

    @Override
    public Object[] generateRow() throws IOException {
        Random random = getRandom();
        byte[] buffer = new byte[32];
        random.nextBytes(buffer);
        return new Object[] {
                random.nextFloat(), // areaInSqKm
                new BytesArray(buffer, 0, 4).toUtf8(), // continent
                new BytesArray(buffer, 4, 8).toUtf8(), // countryCode
                new BytesArray(buffer, 8, 24).toUtf8(), // countryName
                random.nextInt(Integer.MAX_VALUE) // population
        };
    }

    @Override
    public boolean generateData() {
        return true;
    }

    @Override
    protected void createTable() {
        execute("create table \"" + TABLE_NAME + "\" (" +
                " \"areaInSqKm\" float," +
                " capital string," +
                " continent string," +
                " \"continentName\" string," +
                " \"countryCode\" string," +
                " \"countryName\" string," +
                " north float," +
                " east float," +
                " south float," +
                " west float," +
                " \"fipsCode\" string," +
                " \"currencyCode\" string," +
                " languages string," +
                " \"isoAlpha3\" string," +
                " \"isoNumeric\" string," +
                " population integer" +
                ") clustered into 1 shards with (number_of_replicas=0)", new Object[0]);
        ensureGreen();
    }
}
