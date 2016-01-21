package io.crate.benchmark;

import io.crate.testing.CrateTestCluster;
import io.crate.testserver.shade.org.elasticsearch.common.settings.Settings;

import java.net.MalformedURLException;
import java.net.URL;

public class TestsUtils {

    public static final String CRATE_FROM_VERSION_PROPERTY = System.getProperty("crate.version");
    public static final String CRATE_FROM_URL_PROPERTY = System.getProperty("crate.url");

    public static CrateTestCluster testCluster(String clusterName, Settings settings, int numNodes) {
        CrateTestCluster.Builder builder = CrateTestCluster.builder(clusterName)
                .settings(settings)
                .numberOfNodes(numNodes);

        if (CRATE_FROM_URL_PROPERTY != null) {
            URL url = url(CRATE_FROM_URL_PROPERTY);
            return builder.fromURL(url).build();
        }
        return builder.fromFile(CRATE_FROM_VERSION_PROPERTY).build();
    }

    private static URL url(String crateDownloadURL) {
        try {
            return new URL(crateDownloadURL);
        } catch (MalformedURLException e) {
            throw new RuntimeException(String.format("Cannot download crate from URL: %s", crateDownloadURL), e);
        }
    }

}
