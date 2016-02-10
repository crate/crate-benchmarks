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

import com.carrotsearch.junitbenchmarks.BenchmarkRule;
import com.carrotsearch.randomizedtesting.RandomizedTest;
import com.carrotsearch.randomizedtesting.annotations.ThreadLeakScope;
import io.crate.action.sql.SQLBulkRequest;
import io.crate.action.sql.SQLBulkResponse;
import io.crate.action.sql.SQLRequest;
import io.crate.action.sql.SQLResponse;
import io.crate.client.CrateClient;
import io.crate.shade.com.google.common.base.Joiner;
import io.crate.shade.com.google.common.base.MoreObjects;
import io.crate.shade.com.google.common.base.Preconditions;
import io.crate.shade.org.elasticsearch.client.transport.TransportClient;
import io.crate.shade.org.elasticsearch.common.logging.ESLogger;
import io.crate.shade.org.elasticsearch.common.logging.Loggers;
import io.crate.shade.org.elasticsearch.common.settings.ImmutableSettings;
import io.crate.shade.org.elasticsearch.common.transport.InetSocketTransportAddress;
import io.crate.shade.org.elasticsearch.common.unit.TimeValue;
import io.crate.testing.CrateTestCluster;
import io.crate.testing.CrateTestServer;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Ignore;
import org.junit.Rule;

import java.io.IOException;
import java.util.Collections;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.hamcrest.core.Is.is;
import static org.hamcrest.core.IsNull.nullValue;
import static org.junit.Assert.assertThat;


@Ignore
@ThreadLeakScope(value = ThreadLeakScope.Scope.NONE)
public abstract class BenchmarkBase extends RandomizedTest {

    private static final String SQL_REQUEST_TIMEOUT = "CRATE_TESTS_SQL_REQUEST_TIMEOUT";
    private static final TimeValue REQUEST_TIMEOUT = new TimeValue(Long.parseLong(
            MoreObjects.firstNonNull(System.getenv(SQL_REQUEST_TIMEOUT), "1")), TimeUnit.MINUTES);

    public static final String TABLE_NAME = "countries";
    public static final String DATA = "/setup/data/bench.json";

    public static final String CLUSTER_NAME = "benchmarks";
    public static final String CRATE_VERSION = System.getProperty("crate.version");

    @ClassRule
    public static CrateTestCluster testCluster = CrateTestCluster
            .fromVersion(CRATE_VERSION)
            .clusterName(CLUSTER_NAME)
            .settings(io.crate.testserver.shade.org.elasticsearch.common.settings.ImmutableSettings.builder()
                    .put("index.store.type", "memory")
                    .build())
            .numberOfNodes(2)
            .build();

    @Rule
    public BenchmarkRule benchmarkRun = new BenchmarkRule();


    protected TransportClient esClient = null;
    protected static CrateClient crateClient;

    public final ESLogger logger = Loggers.getLogger(getClass());

    protected SQLResponse execute(String statement) {
        return execute(statement, SQLRequest.EMPTY_ARGS, REQUEST_TIMEOUT);
    }

    protected SQLResponse execute(String statement, TimeValue timeout) {
        return execute(statement, SQLRequest.EMPTY_ARGS, timeout);
    }

    protected SQLResponse execute(String statement, Object[] args) {
        return execute(statement, args, REQUEST_TIMEOUT);
    }

    protected SQLResponse execute(String statement, Object[] args, TimeValue timeout) {
        return crateClient.sql(new SQLRequest(statement, args)).actionGet(timeout);
    }

    protected SQLBulkResponse execute(String statement, Object[][] bulkArgs) {
        return execute(statement, bulkArgs, REQUEST_TIMEOUT);
    }

    protected SQLBulkResponse execute(String statement, Object[][] bulkArgs, TimeValue timeout) {
        return crateClient.bulkSql(new SQLBulkRequest(statement, bulkArgs)).actionGet(timeout.getMillis());
    }

    protected void ensureGreen() {
        esClient.admin().cluster().prepareHealth().setWaitForGreenStatus().execute().actionGet();
    }

    @BeforeClass
    public static void init() {
        String[] servers  = testCluster.servers().stream()
                .map(server -> String.format("%s:%d", server.crateHost(), server.transportPort()))
                .toArray(String[]::new);
        crateClient = new CrateClient(servers);
    }

    @Before
    public void setUp() throws Exception {
        if (esClient == null) {
            esClient = new TransportClient(ImmutableSettings.builder().put("cluster.name", CLUSTER_NAME).build());
            for (CrateTestServer server : testCluster.servers()) {
                InetSocketTransportAddress serverAdress = new InetSocketTransportAddress(server.crateHost(), server.transportPort());
                esClient.addTransportAddress(serverAdress);
            }
        }
        if (!indexExists()) {
            createTable();
            if (importData()) {
                doImportData();
            } else if (generateData()) {
                doGenerateData();
            }
        }
    }

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
                " south float," +
                " west float" +
                ") clustered into 2 shards with (number_of_replicas=0)", new Object[0]);
        ensureGreen();
    }

    protected void doGenerateData() throws Exception {
        final String tableName = tableName();
        final int numberOfDocuments = numberOfDocuments();
        logger.info("generating {} documents...", numberOfDocuments);
        ExecutorService executor = Executors.newFixedThreadPool(4);
        for (int i=0; i<4; i++) {
            executor.submit(() -> {
                    int numDocsToCreate = numberOfDocuments/4;
                    logger.info("Generating {} Documents in Thread {}", numDocsToCreate, Thread.currentThread().getName());
                    for (int j=0; j < numDocsToCreate; j+=1000) {
                        Object[][] bulkArgs = new Object[1000][];
                        try {
                            Object[] row = null;
                            if (!generateNewRowForEveryDocument()) {
                                row = generateRow();
                            }
                            for (int k=0; k<1000;k++) {
                                if (generateNewRowForEveryDocument()) {
                                    row = generateRow();
                                }
                                bulkArgs[k] = row;
                            }
                            insertRows(tableName, bulkArgs);
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                });
        }
        executor.shutdown();
        executor.awaitTermination(2L, TimeUnit.MINUTES);
        executor.shutdownNow();
        refresh(tableName);
        logger.info("{} documents generated.", numberOfDocuments);
    }

    private void insertRows(String tableName, Object[][] bulkArgs) {
        Preconditions.checkArgument(bulkArgs.length > 0, "will not insert empty rows");
        int rowWidth = bulkArgs[0].length;
        String params = Joiner.on(",").join(Collections.nCopies(rowWidth, "?"));
        String stmt = String.format(Locale.ENGLISH, "INSERT INTO \"%s\" VALUES (%s)", tableName, params);
        SQLBulkResponse bulkResponse = execute(stmt, bulkArgs);
        for (SQLBulkResponse.Result result : bulkResponse.results()) {
            assertThat(result.errorMessage(), is(nullValue()));
        }
    }

    /**
     * needs to create rows with values in order of their appearance in the table
     */
    protected Object[] generateRow() throws IOException {
        return new Object[0];
    }

    protected boolean generateNewRowForEveryDocument() {
        return false;
    }

    protected void refresh(String table) {
        execute(String.format(Locale.ENGLISH, "REFRESH TABLE \"%s\"", table));
    }

    public boolean indexExists() {
        String[] parts = tableName().split("\\.", 1);
        String schemaName = parts.length == 2 ? parts[0] : "doc";
        String tableName = parts.length == 2 ? parts[1] : parts[0];
        SQLResponse response = execute("select * from information_schema.tables where schema_name=? AND table_name=?",
                new Object[]{
                       schemaName,
                       tableName
                });
        return response.rowCount() > 0;
    }

    public boolean importData() {
        return false;
    }

    public boolean generateData() {
        return false;
    }

    protected int numberOfDocuments() {
        return 0;
    }

    protected String tableName() {
        return TABLE_NAME;
    }

    protected String dataPath() {
        return DATA;
    }

    public void doImportData() throws Exception {
        loadBulk();
        refresh(tableName());
    }

    public void loadBulk() throws Exception {
        String pathUri = "file://" + getClass().getResource(dataPath()).toURI().getPath();
        SQLResponse sqlResponse = execute(String.format(Locale.ENGLISH, "COPY \"%s\" FROM ? WITH (shared=true)", tableName()), new Object[]{ pathUri });
        if (sqlResponse.rowCount() <= 0L) {
            throw new IllegalStateException("loadBulk failed importing");
        }
    }
}
