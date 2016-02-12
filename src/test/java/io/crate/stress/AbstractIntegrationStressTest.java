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

package io.crate.stress;

import com.carrotsearch.randomizedtesting.RandomizedTest;
import com.carrotsearch.randomizedtesting.annotations.ThreadLeakScope;
import io.crate.action.sql.SQLBulkRequest;
import io.crate.action.sql.SQLBulkResponse;
import io.crate.action.sql.SQLRequest;
import io.crate.action.sql.SQLResponse;
import io.crate.client.CrateClient;
import io.crate.concurrent.ThreadedExecutionRule;
import io.crate.shade.com.google.common.base.MoreObjects;
import io.crate.shade.com.google.common.util.concurrent.SettableFuture;
import io.crate.shade.org.elasticsearch.action.ActionFuture;
import io.crate.shade.org.elasticsearch.client.transport.TransportClient;
import io.crate.shade.org.elasticsearch.common.settings.ImmutableSettings;
import io.crate.shade.org.elasticsearch.common.transport.InetSocketTransportAddress;
import io.crate.shade.org.elasticsearch.common.unit.TimeValue;
import io.crate.testing.CrateTestCluster;
import io.crate.testing.CrateTestServer;
import org.junit.After;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Rule;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

@ThreadLeakScope(ThreadLeakScope.Scope.NONE)
public abstract class AbstractIntegrationStressTest extends RandomizedTest {

    private static final String SQL_REQUEST_TIMEOUT = "CRATE_TESTS_SQL_REQUEST_TIMEOUT";
    private static final TimeValue REQUEST_TIMEOUT = new TimeValue(Long.parseLong(
            MoreObjects.firstNonNull(System.getenv(SQL_REQUEST_TIMEOUT), "5")), TimeUnit.SECONDS);

    public static final String CLUSTER_NAME = "stress";

    @ClassRule
    public static CrateTestCluster testCluster;

    @Rule
    public ThreadedExecutionRule threadedExecutionRule = new ThreadedExecutionRule();

    private final AtomicBoolean firstPrepared = new AtomicBoolean(false);
    private final SettableFuture<Void> preparedFuture = SettableFuture.create();
    private final AtomicInteger stillRunning = new AtomicInteger(0);
    private final SettableFuture<Void> cleanUpFuture = SettableFuture.create();
    protected static CrateClient crateClient;
    protected TransportClient esClient = null;

    /**
     * preparation only executed in the first thread that reaches @Before
     */
    public void prepareFirst() throws Exception {}

    /**
     * cleanup only executed by the last thread that reaches @After
     */
    public void cleanUpLast() throws Exception {}

    @BeforeClass
    public static void init() {
        String[] servers  = testCluster.servers().stream()
                .map(server -> String.format("%s:%d", server.crateHost(), server.transportPort()))
                .toArray(String[]::new);
        crateClient = new CrateClient(servers);
    }

    @Before
    public void delegateToPrepareFirst() throws Exception {
        if (esClient == null) {
            esClient = new TransportClient(ImmutableSettings.builder().put("cluster.name", CLUSTER_NAME).build());
            for (CrateTestServer server : testCluster.servers()) {
                InetSocketTransportAddress serverAdress = new InetSocketTransportAddress(server.crateHost(), server.transportPort());
                esClient.addTransportAddress(serverAdress);
            }
        }
        if (firstPrepared.compareAndSet(false, true)) {
            prepareFirst();
            preparedFuture.set(null);
        } else {
            preparedFuture.get();
        }
        stillRunning.incrementAndGet();
    }

    @After
    public void waitForAllTestsToReachAfter() throws Exception {
        if (stillRunning.decrementAndGet() > 0) {
            cleanUpFuture.get();
        } else {
            // der letzte macht das licht aus
            cleanUpLast();
            cleanUpFuture.set(null);
        }
    }

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

    public ActionFuture<SQLResponse> executeAsync(String statement) {
        return executeAsync(statement, SQLRequest.EMPTY_ARGS);
    }

    public ActionFuture<SQLResponse> executeAsync(String statement, Object[] args) {
        return crateClient.sql(new SQLRequest(statement, args));
    }

    public ActionFuture<SQLBulkResponse> executeAsync(String statement, Object[][] bulkArgs) {
        return crateClient.bulkSql(new SQLBulkRequest(statement, bulkArgs));
    }

    protected void ensureGreen() {
        esClient.admin().cluster().prepareHealth().setWaitForGreenStatus().execute().actionGet();
    }

    protected void ensureYellow() {
        esClient.admin().cluster().prepareHealth().setWaitForYellowStatus().execute().actionGet();
    }

}
