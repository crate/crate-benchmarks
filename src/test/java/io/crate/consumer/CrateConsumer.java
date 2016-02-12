package io.crate.consumer;

import com.carrotsearch.junitbenchmarks.AutocloseConsumer;
import com.carrotsearch.junitbenchmarks.Result;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import io.crate.action.sql.SQLRequest;
import io.crate.client.CrateClient;
import org.apache.log4j.Logger;

import java.io.Closeable;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public final class CrateConsumer extends AutocloseConsumer implements Closeable {

    private final static Logger LOGGER = Logger.getLogger(CrateConsumer.class);

    private static final JsonParser jsonParser = new JsonParser();
    private static final DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssX");

    private final String testServerHost;
    private final int testServerHttpPort;
    private final CrateClient client;

    public CrateConsumer(String testServerHost, int testServerHttpPort) {
        this.testServerHost = testServerHost;
        this.testServerHttpPort = testServerHttpPort;
        client = new CrateClient(composeUrls(getHosts(), getPort(CrateConsumerConstants.CRATE_TRANSPORT_PORT)));
        client.sql(CrateConsumerConstants.CREATE_TABLE_IF_NOT_EXISTS_STMT).actionGet();
    }

    private static String[] getHosts() {
        final String hostsStr = System.getProperty(CrateConsumerConstants.CRATE_HOST);
        if (hostsStr != null && !hostsStr.trim().equals("")) {
            return hostsStr.split(",");
        }
        throw new IllegalArgumentException(String
                .format("Missing global property: %s", CrateConsumerConstants.CRATE_HOST));
    }

    private static int getPort(String portProperty) {
        final String port = System.getProperty(portProperty);
        if (port != null && !port.trim().equals("")) {
            return Integer.valueOf(port);
        }
        throw new IllegalArgumentException(String
                .format("Missing global property: %s", portProperty));
    }

    private static String[] composeUrls(String[] hosts, int port) {
        return Arrays.stream(hosts)
                .map(host -> String.format("http://%s:%d", host, port))
                .toArray(String[]::new);
    }

    @Override
    public void accept(Result result) throws IOException {
        try {
            JsonObject versionInfo = clusterVersionInfo();

            Object[] args = new Object[]{
                    result.getShortTestClassName(),
                    result.getTestMethodName(),
                    crateBuildVersion(versionInfo),
                    crateBuildTimestamp(versionInfo),
                    System.currentTimeMillis(),
                    benchmarkValues(result)
            };
            client.sql(new SQLRequest(CrateConsumerConstants.INSERT_STMT, args)).actionGet();
        } catch (ParseException e) {
            LOGGER.warn("Cannot parse timestamp: ", e);
        } catch (IOException e) {
            LOGGER.warn("Error while fetching crate build timestamp: ", e);
        } catch (Exception e) {
            LOGGER.warn("Result of benchmark run is not inserted: ", e);
        }
    }

    private static Map<String, Object> benchmarkValues(Result result) {
        return new HashMap<String, Object>() {{
            put("benchmark_rounds", result.benchmarkRounds);
            put("warmup_rounds", result.warmupRounds);
            put("round_avg", result.roundAverage.avg);
            put("round_stddev", result.roundAverage.stddev);
            put("gc_avg", result.gcAverage.avg);
            put("gc_stddev", result.gcAverage.stddev);
            put("gc_invocations", result.gcInfo.accumulatedInvocations());
            put("gc_time", result.gcInfo.accumulatedTime());
            put("benchmark_time_total", result.benchmarkTime);
            put("warmup_time_total", result.warmupTime);
        }};
    }

    private JsonObject clusterVersionInfo() throws IOException {
        URL url = new URL(String.format("http://%s:%d", testServerHost, testServerHttpPort));
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.connect();
        JsonElement root = jsonParser.parse(new InputStreamReader((InputStream) connection.getContent()));
        return root.getAsJsonObject()
                .get("version").getAsJsonObject();
    }

    private long crateBuildTimestamp(JsonObject versionInfo) throws ParseException, IOException {
        return parseTimestamp(versionInfo.get("build_timestamp").getAsString());
    }

    private String crateBuildVersion(JsonObject versionInfo) {
        return versionInfo.get("number").getAsString();
    }


    private static long parseTimestamp(String timestamp) throws ParseException {
        return dateFormat.parse(timestamp).getTime();
    }

    @Override
    public void close() throws IOException {
        if (client != null) {
            client.close();
        }
    }

}
