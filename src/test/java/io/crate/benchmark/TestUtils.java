package io.crate.benchmark;

import io.crate.testing.CrateTestCluster;
import io.crate.testserver.shade.org.elasticsearch.common.settings.Settings;

import java.net.MalformedURLException;
import java.net.URL;

public class TestUtils {
    public static final String CRATE_FROM_VERSION_PROPERTY = System.getProperty("crate.version", null);
    public static final String CRATE_FROM_URL_PROPERTY = System.getProperty("crate.url", null);

    public static CrateTestCluster testCluster(String clusterName, Settings settings, int numNodes) {
        CrateTestCluster.Builder builder = CrateTestCluster.builder(clusterName);

        if (CRATE_FROM_URL_PROPERTY != null && !CRATE_FROM_URL_PROPERTY.trim().isEmpty()) {
            builder.fromURL(makeUrl(CRATE_FROM_URL_PROPERTY));
        } else if (CRATE_FROM_VERSION_PROPERTY != null && !CRATE_FROM_VERSION_PROPERTY.trim().isEmpty()) {
            builder.fromVersion(CRATE_FROM_VERSION_PROPERTY);
        } else {
            throw new RuntimeException("Crate version or URL path to the crate .tar.gz is not provided!");
        }
        return builder
                .settings(settings)
                .numberOfNodes(numNodes).build();
    }

    private static URL makeUrl(String crateDownloadURL) {
        try {
            return new URL(crateDownloadURL);
        } catch (MalformedURLException e) {
            throw new RuntimeException(String.format("Cannot download crate from URL: %s", crateDownloadURL), e);
        }
    }
}
