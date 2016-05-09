package io.crate.consumer;

import com.carrotsearch.junitbenchmarks.AutocloseConsumer;
import com.carrotsearch.junitbenchmarks.Result;
import com.google.gson.*;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.log4j.Logger;

import java.io.Closeable;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.HashMap;
import java.util.Map;

public final class CrateConsumer extends AutocloseConsumer implements Closeable {

    private final static Logger LOGGER = Logger.getLogger(CrateConsumer.class);

    private static final JsonParser jsonParser = new JsonParser();
    private static final DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssX");

    private final String testServerHost;
    private final int testServerHttpPort;
    private final HttpClient httpClient;
    private final Gson gson = new GsonBuilder().create();

    public CrateConsumer(String testServerHost, int testServerHttpPort) {
        this.httpClient = HttpClientBuilder.create().build();
        this.testServerHost = testServerHost;
        this.testServerHttpPort = testServerHttpPort;
    }

    private static String getHost() {
        final String hostsStr = System.getProperty(CrateConsumerConstants.CRATE_HOST);
        if (hostsStr != null && !hostsStr.trim().equals("")) {
            return hostsStr;
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

    private static String composeURI(String host, int port) {
        return String.format("http://%s:%d/_sql", host, port);
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
            JsonObject content = new JsonObject();
            content.add("args", gson.toJsonTree(args));
            content.addProperty("stmt", CrateConsumerConstants.INSERT_STMT);
            HttpPost request = new HttpPost(composeURI(getHost(), getPort(CrateConsumerConstants.CRATE_HTTP_PORT)));
            request.setEntity(new StringEntity(gson.toJson(content)));
            HttpResponse res = httpClient.execute(request);
            if (res.getStatusLine().getStatusCode() != 200) {
                LOGGER.error("Failed to store benchmark result");
            }
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
        HttpGet request = new HttpGet(composeURI(testServerHost, testServerHttpPort));
        HttpResponse response = httpClient.execute(request);
        JsonElement root = jsonParser.parse(new InputStreamReader(response.getEntity().getContent()));
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
    }

}
