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

import com.carrotsearch.randomizedtesting.annotations.Repeat;
import io.crate.benchmark.TestsUtils;
import io.crate.concurrent.Threaded;
import io.crate.testserver.action.sql.SQLResponse;
import io.crate.testserver.shade.org.elasticsearch.common.settings.ImmutableSettings;
import org.junit.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.core.Is.is;

public class SysClusterStressTest extends AbstractIntegrationStressTest {

    static {
        cluster = TestsUtils.testCluster(
                CLUSTER_NAME,
                ImmutableSettings.builder().build(),
                2
        );
    }

    @Test
    @Repeat(iterations = 10)
    @Threaded(count = 2)
    public void testSelectStarFromSysCluster() throws Exception {
        SQLResponse sqlResponse = execute("select * from sys.cluster");
        assertThat(sqlResponse.rowCount(), is(1L));
    }
}
