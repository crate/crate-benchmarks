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

package io.crate.stress;

import com.carrotsearch.randomizedtesting.annotations.Repeat;
import io.crate.action.sql.SQLRequest;
import io.crate.action.sql.SQLResponse;
import io.crate.client.CrateClient;
import io.crate.shade.org.elasticsearch.common.unit.TimeValue;
import io.crate.shade.org.elasticsearch.common.util.concurrent.EsExecutors;
import io.crate.testing.CrateTestCluster;
import io.crate.testing.CrateTestServer;
import org.junit.Before;
import org.junit.Test;

import java.util.Iterator;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class ConcurrentCopyFromTest extends AbstractIntegrationStressTest {

    static {
        testCluster = CrateTestCluster
                .fromSysProperties()
                .clusterName(CLUSTER_NAME)
                .numberOfNodes(2)
                .build();
    }

    @Before
    public void prepareFirst() throws Exception {
        execute("DROP TABLE IF EXISTS concurrent_cp");
        execute("CREATE TABLE concurrent_cp\n" +
                "(\n" +
                "    user_id long primary key,\n" +
                "    begin timestamp primary key,\n" +
                "    ev_id long primary key,\n" +
                "    csp_id int,\n" +
                "    updated timestamp,\n" +
                "    tenant int,\n" +
                "    count long,\n" +
                "    bytes long,\n" +
                "    up long,\n" +
                "    down long,\n" +
                "    \"end\" timestamp\n" +
                ") CLUSTERED BY (user_id) INTO 30 SHARDS PARTITIONED BY (begin)\n" +
                "  WITH (column_policy = 'strict', number_of_replicas=0)");
        ensureGreen();
    }

    @Repeat(iterations=10)
    @Test
    public void testConcurrentCopyFrom() throws Exception {
        ThreadPoolExecutor executor = EsExecutors.newFixed(2, 2, EsExecutors.daemonThreadFactory("COPY FROM"));
        final Iterator<CrateTestServer> serverIt = testCluster.servers().iterator();
        final String copyFromSource0 = ConcurrentCopyFromTest.class.getResource("concurrent_copy_from_0.json.gz").getPath();
        final String copyFromSource3 = ConcurrentCopyFromTest.class.getResource("concurrent_copy_from_3.json.gz").getPath();
        try {
            executor.execute(() -> {
                CrateTestServer server = serverIt.next();
                CrateClient crateClient = new CrateClient(String.format("%s:%d", server.crateHost(), server.transportPort()));
                SQLResponse response = crateClient.sql(new SQLRequest("COPY concurrent_cp FROM ? with (shared=true, compression='gzip', bulk_size=100)",
                        new Object[]{copyFromSource0})).actionGet(TimeValue.timeValueMinutes(4));
                System.out.println(String.format("ROWS: %s DURATION: %s", response.rowCount(), response.duration()));
            });
            executor.execute(() -> {
                CrateTestServer server = serverIt.next();
                CrateClient crateClient = new CrateClient(String.format("%s:%d", server.crateHost(), server.transportPort()));
                SQLResponse response = crateClient.sql(new SQLRequest("COPY concurrent_cp FROM ? with (shared=true, compression='gzip', bulk_size=100)",
                        new Object[]{copyFromSource3})).actionGet(TimeValue.timeValueMinutes(4));
                System.out.println(String.format("ROWS: %s DURATION: %s", response.rowCount(), response.duration()));
            });
            executor.shutdown();
            executor.awaitTermination(10, TimeUnit.MINUTES);
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            executor.shutdownNow();
        }
    }
}
