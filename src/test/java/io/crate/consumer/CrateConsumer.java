package io.crate.consumer;

import com.carrotsearch.junitbenchmarks.AutocloseConsumer;
import com.carrotsearch.junitbenchmarks.Result;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import io.crate.testserver.action.sql.SQLRequest;
import io.crate.testserver.action.sql.SQLResponse;
import io.crate.testserver.client.CrateClient;
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
import java.util.stream.Stream;

public final class CrateConsumer extends AutocloseConsumer implements Closeable {

    private final static Logger LOGGER = Logger.getLogger(CrateConsumer.class);

    private final JsonParser jsonParser = new JsonParser();
    private final DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssX");

    private CrateClient client;

    private String[] hosts;
    private int transportPort;
    private int httpPort;

    public CrateConsumer() {
        this.httpPort = getPort(CrateConsumerConstants.CRATE_HTTP_PORT);
        this.transportPort = getPort(CrateConsumerConstants.CRATE_TRANSPORT_PORT);
        this.hosts = getHosts();

        client = new CrateClient(
                composeUrls(hosts, transportPort).toArray(String[]::new)
        );
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

    private int getPort(String portProperty) {
        final String port = System.getProperty(portProperty);
        if (port != null && !port.trim().equals("")) {
            return Integer.valueOf(port);
        }
        throw new IllegalArgumentException(String
                .format("Missing global property: %s", portProperty));
    }

    private Stream<String> composeUrls(String[] hosts, int port) {
        return Arrays.stream(hosts)
                .map(host -> String.format("http://%s:%d", host, port));
    }

    @Override
    public void accept(Result result) throws IOException {
        try {
            Object[] args = new Object[]{
                    result.getTestClassName(),
                    result.getTestMethodName(),
                    crateBuildVersion(),
                    crateBuildTimestamp(),
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

    private Map<String, Object> benchmarkValues(Result result) {
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

    private String crateBuildVersion() {
        SQLResponse response = client.sql(CrateConsumerConstants.SELECT_VERSIONS).actionGet();
        Object[][] rows = response.rows();
        assert rows.length != 0;
        checkClusterVersionsHomogeneity(rows);
        return String.valueOf(rows[0][0]);
    }

    private void checkClusterVersionsHomogeneity(Object[][] rows) {
        String firstFetchVersion = String.valueOf(rows[0][0]);
        boolean check = Arrays.stream(rows)
                .map(row -> row[0])
                .allMatch(version -> version.equals(firstFetchVersion));
        if (!check) {
            throw new RuntimeException("Cluster contains nodes with different crate versions");
        }
    }

    private long crateBuildTimestamp() throws ParseException, IOException {
        URL url = new URL(
                composeUrls(hosts, httpPort).findAny().get()
        );
        HttpURLConnection request = (HttpURLConnection) url.openConnection();
        request.connect();

        JsonElement root = jsonParser.parse(new InputStreamReader((InputStream) request.getContent()));
        String timestamp = root.getAsJsonObject()
                .get("version").getAsJsonObject()
                .get("build_timestamp").getAsString();
        return parseTimestamp(timestamp);
    }

    private long parseTimestamp(String timestamp) throws ParseException {
        return dateFormat.parse(timestamp).getTime();
    }

    @Override
    public void close() throws IOException {
        if (client != null) {
            client.close();
            client = null;
        }
    }
}
