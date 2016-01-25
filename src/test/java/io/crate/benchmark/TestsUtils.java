package io.crate.benchmark;

import io.crate.testing.CrateTestCluster;
import io.crate.testserver.shade.org.elasticsearch.common.settings.Settings;

import java.net.MalformedURLException;
import java.net.URL;

public class TestsUtils {

    public static final String CRATE_FROM_VERSION_PROPERTY = System.getProperty("crate.version");
    public static final String CRATE_FROM_URL_PROPERTY = System.getProperty("crate.url");
    static {
        System.out.print(CRATE_FROM_URL_PROPERTY);
    }

    public static CrateTestCluster testCluster(String clusterName, Settings settings, int numNodes) {
        CrateTestCluster.Builder builder = CrateTestCluster.builder(clusterName);


        if (CRATE_FROM_URL_PROPERTY != null) {
            builder.fromURL(makeUrl(CRATE_FROM_URL_PROPERTY));
        } else {
            builder.fromFile(CRATE_FROM_VERSION_PROPERTY);
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
