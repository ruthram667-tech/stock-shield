package com.stockshield.repository;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.QueryApi;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.*;

/**
 * Custom repository for reading/writing time-series telemetry data to InfluxDB.
 */
@Repository
@RequiredArgsConstructor
@Slf4j
public class TelemetryRepository {

    private final InfluxDBClient influxDBClient;

    @Value("${influxdb.bucket}")
    private String bucket;

    @Value("${influxdb.org}")
    private String org;

    /**
     * Write a weight reading to InfluxDB.
     */
    public void writeWeight(String shelfId, String itemId, double weightKg) {
        try {
            WriteApiBlocking writeApi = influxDBClient.getWriteApiBlocking();
            Point point = Point.measurement("weight")
                    .addTag("shelfId", shelfId)
                    .addTag("itemId", itemId)
                    .addField("value", weightKg)
                    .time(Instant.now(), WritePrecision.MS);
            writeApi.writePoint(bucket, org, point);
        } catch (Exception e) {
            log.error("Failed to write weight to InfluxDB: {}", e.getMessage());
        }
    }

    /**
     * Write environment (temp + humidity) reading to InfluxDB.
     */
    public void writeEnvironment(String shelfId, double tempC, double humidityPct) {
        try {
            WriteApiBlocking writeApi = influxDBClient.getWriteApiBlocking();
            Point point = Point.measurement("environment")
                    .addTag("shelfId", shelfId)
                    .addField("temperature", tempC)
                    .addField("humidity", humidityPct)
                    .time(Instant.now(), WritePrecision.MS);
            writeApi.writePoint(bucket, org, point);
        } catch (Exception e) {
            log.error("Failed to write environment to InfluxDB: {}", e.getMessage());
        }
    }

    /**
     * Query weight history for a shelf over a time range.
     *
     * @param shelfId the shelf identifier
     * @param range   Flux duration string (e.g. "24h", "7d", "30d")
     * @return list of {time, value} maps
     */
    public List<Map<String, Object>> queryWeightHistory(String shelfId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"weight\") " +
                "|> filter(fn: (r) => r.shelfId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, shelfId
        );
        return executeQuery(flux);
    }

    /**
     * Query environment (temp/humidity) history for a shelf.
     */
    public List<Map<String, Object>> queryEnvironmentHistory(String shelfId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"environment\") " +
                "|> filter(fn: (r) => r.shelfId == \"%s\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, shelfId
        );
        return executeQuery(flux);
    }

    /**
     * Query weight data formatted for the ML service (daily aggregates).
     */
    public List<Map<String, Object>> queryWeightForML(String itemId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"weight\") " +
                "|> filter(fn: (r) => r.itemId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 1h, fn: mean, createEmpty: false) " +
                "|> yield(name: \"hourly_mean\")",
                bucket, range, itemId
        );
        return executeQuery(flux);
    }

    private List<Map<String, Object>> executeQuery(String flux) {
        List<Map<String, Object>> results = new ArrayList<>();
        try {
            QueryApi queryApi = influxDBClient.getQueryApi();
            List<FluxTable> tables = queryApi.query(flux, org);
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("time", record.getTime());
                    row.put("field", record.getField());
                    row.put("value", record.getValue());
                    if (record.getValueByKey("shelfId") != null) {
                        row.put("shelfId", record.getValueByKey("shelfId"));
                    }
                    if (record.getValueByKey("itemId") != null) {
                        row.put("itemId", record.getValueByKey("itemId"));
                    }
                    results.add(row);
                }
            }
        } catch (Exception e) {
            log.error("InfluxDB query failed: {}", e.getMessage());
        }
        return results;
    }
}
