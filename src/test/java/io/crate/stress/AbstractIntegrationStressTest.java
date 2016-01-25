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
import io.crate.concurrent.ThreadedExecutionRule;
import io.crate.testing.CrateTestCluster;
import io.crate.testserver.action.sql.SQLBulkResponse;
import io.crate.testserver.action.sql.SQLRequest;
import io.crate.testserver.action.sql.SQLResponse;
import io.crate.testserver.shade.com.google.common.base.MoreObjects;
import io.crate.testserver.shade.com.google.common.util.concurrent.SettableFuture;
import io.crate.testserver.shade.org.elasticsearch.common.unit.TimeValue;
import org.junit.After;
import org.junit.Before;
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
    public static CrateTestCluster cluster;

    @Rule
    public ThreadedExecutionRule threadedExecutionRule = new ThreadedExecutionRule();

    private final AtomicBoolean firstPrepared = new AtomicBoolean(false);
    private final SettableFuture<Void> preparedFuture = SettableFuture.create();
    private final AtomicInteger stillRunning = new AtomicInteger(0);
    private final SettableFuture<Void> cleanUpFuture = SettableFuture.create();


    /**
     * preparation only executed in the first thread that reaches @Before
     */
    public void prepareFirst() throws Exception {}

    /**
     * cleanup only executed by the last thread that reaches @After
     */
    public void cleanUpLast() throws Exception {}

    @Before
    public void delegateToPrepareFirst() throws Exception {
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

    public SQLResponse execute(String stmt) {
        return execute(stmt, SQLRequest.EMPTY_ARGS, REQUEST_TIMEOUT);
    }

    public SQLResponse execute(String stmt, Object[] args) {
        return execute(stmt, args, REQUEST_TIMEOUT);
    }

    public SQLResponse execute(String stmt, TimeValue timeout) {
        return execute(stmt, SQLRequest.EMPTY_ARGS, timeout);
    }

    public SQLResponse execute(String stmt, Object[] args, TimeValue timeout) {
        return cluster.execute(stmt, args, timeout);
    }

    public SQLBulkResponse execute(String stmt, Object[][] bulkArgs) {
        return execute(stmt, bulkArgs, REQUEST_TIMEOUT);
    }

    public SQLBulkResponse execute(String stmt, Object[][] bulkArgs, TimeValue timeout) {
        return cluster.execute(stmt, bulkArgs, timeout);
    }

    public void ensureGreen() {
        cluster.ensureGreen();
    }

    public void ensureYellow() {
        cluster.ensureYellow();
    }
}
