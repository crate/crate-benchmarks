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
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkHistoryChart;
import com.carrotsearch.junitbenchmarks.annotation.BenchmarkMethodChart;
import com.carrotsearch.junitbenchmarks.annotation.LabelType;
import io.crate.testserver.action.sql.SQLBulkResponse;
import io.crate.testserver.shade.org.elasticsearch.action.search.SearchResponse;
import io.crate.testserver.shade.org.elasticsearch.common.bytes.BytesArray;
import io.crate.testserver.shade.org.elasticsearch.common.logging.ESLogger;
import io.crate.testserver.shade.org.elasticsearch.common.logging.Loggers;
import io.crate.testserver.shade.org.elasticsearch.search.sort.SortBuilders;
import org.junit.Test;

import java.io.IOException;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.core.Is.is;
import static org.hamcrest.core.IsNull.nullValue;


@BenchmarkHistoryChart(filePrefix="benchmark-lucenedoccollector-history", labelWith = LabelType.CUSTOM_KEY)
@BenchmarkMethodChart(filePrefix = "benchmark-lucenedoccollector")
public class ESScrollingBenchmark extends BenchmarkBase {

    public static boolean dataGenerated = false;
    public static final int NUMBER_OF_DOCUMENTS = 100_000;
    public static final int BENCHMARK_ROUNDS = 100;
    public static final int WARMUP_ROUNDS = 10;
    // should be in-sync with sql->Paging.PAGE_SIZE
    public static final int PAGE_SIZE = 500_000;

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
        testCluster.ensureGreen();
    }

    @Override
    protected void doGenerateData() throws Exception {
        if (!dataGenerated) {

            logger.info("generating {} documents...", NUMBER_OF_DOCUMENTS);
            ExecutorService executor = Executors.newFixedThreadPool(4);
            for (int _thread=0; _thread<4; _thread++) {
                executor.submit(() -> {
                        int numDocsToCreate = NUMBER_OF_DOCUMENTS/4;
                        logger.info("Generating {} Documents in Thread {}", numDocsToCreate, Thread.currentThread().getName());
                        for (int i=0; i < numDocsToCreate; i+=1000) {
                            Object[][] bulkArgs = new Object[1000][];
                            try {
                                Object[] row = generateRow();
                                for (int j=0; j<1000;j++) {
                                    bulkArgs[j] = row;
                                }
                                SQLBulkResponse bulkResponse = execute(
                                        "INSERT INTO \"" + TABLE_NAME + "\" (\"areaInSqKm\", continent, \"countryCode\", \"countryName\", population) VALUES (?, ?, ?, ?, ?)",
                                        bulkArgs);
                                for (SQLBulkResponse.Result result : bulkResponse.results()) {
                                    assertThat(result.errorMessage(), is(nullValue()));
                                }
                            } catch (IOException e) {
                                e.printStackTrace();
                            }
                        }
                });
            }
            executor.shutdown();
            executor.awaitTermination(2L, TimeUnit.MINUTES);
            executor.shutdownNow();
            esClient.admin().indices().prepareFlush(TABLE_NAME).execute().actionGet();
            refresh(TABLE_NAME);
            dataGenerated = true;
            logger.info("{} documents generated.", NUMBER_OF_DOCUMENTS);
        }
    }

    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = WARMUP_ROUNDS)
    @Test
    public void testElasticsearchOrderedWithScrollingPerformance() throws Exception{
        int totalHits = 0;
        SearchResponse response = esClient.prepareSearch(TABLE_NAME).setTypes("default")
                                    .addField("continent")
                                    .addSort(SortBuilders.fieldSort("continent").missing("_last"))
                                    .setScroll("1m")
                                    .setSize(PAGE_SIZE)
                                    .execute().actionGet();
        totalHits += response.getHits().hits().length;
        while ( totalHits < NUMBER_OF_DOCUMENTS) {
            response = esClient.prepareSearchScroll(response.getScrollId()).setScroll("1m").execute().actionGet();
            totalHits += response.getHits().hits().length;
        }
    }

    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = WARMUP_ROUNDS)
    @Test
    public void testElasticsearchOrderedWithoutScrollingPerformance() throws Exception{
        esClient.prepareSearch(TABLE_NAME).setTypes("default")
                .addField("continent")
                .addSort(SortBuilders.fieldSort("continent").missing("_last"))
                .setSize(NUMBER_OF_DOCUMENTS)
                .execute().actionGet();
    }

    @BenchmarkOptions(benchmarkRounds = BENCHMARK_ROUNDS, warmupRounds = WARMUP_ROUNDS)
    @Test
    public void testElasticsearchUnorderedWithoutScrollingPerformance() throws Exception{
        esClient.prepareSearch(TABLE_NAME).setTypes("default")
                .addField("continent")
                .setSize(NUMBER_OF_DOCUMENTS)
                .execute().actionGet();
    }
}
