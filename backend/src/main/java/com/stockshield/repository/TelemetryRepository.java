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
 * Generic telemetry repository — writes and queries ANY sensor type's data
 * to/from InfluxDB. No longer hardcoded to weight/temperature.
 */
@Repository
@RequiredArgsConstructor
@Slf4j
public class TelemetryRepository {

    private final InfluxDBClient influxDBClient;

    @Value("${influxdb.bucket}")
    private String bucket;

    @Value("${influxdb.org}")
    private String influxOrg;

    // ── Generic Write (works for ANY sensor type) ──────────────────────────

    /**
     * Write a sensor reading to InfluxDB.
     * The measurement name IS the sensor type (temperature, pressure, ph, weight, etc.).
     */
    public void writeGeneric(String tenantId, String locationId,
                              String sensorType, double value) {
        try {
            WriteApiBlocking writeApi = influxDBClient.getWriteApiBlocking();
            Point point = Point.measurement(sensorType)
                    .addTag("tenantId", tenantId)
                    .addTag("locationId", locationId)
                    .addField("value", value)
                    .time(Instant.now(), WritePrecision.MS);
            writeApi.writePoint(bucket, influxOrg, point);
        } catch (Exception e) {
            log.error("Failed to write {} telemetry to InfluxDB: {}", sensorType, e.getMessage());
        }
    }

    // ── Legacy Write Methods (delegate to generic) ────────────────────────

    /**
     * Write a weight reading — legacy method, delegates to generic.
     */
    public void writeWeight(String locationId, String itemId, double weightKg) {
        writeWeight("demo-tenant", locationId, itemId, weightKg);
    }

    public void writeWeight(String tenantId, String locationId, String itemId, double weightKg) {
        try {
            WriteApiBlocking writeApi = influxDBClient.getWriteApiBlocking();
            Point point = Point.measurement("weight")
                    .addTag("tenantId", tenantId)
                    .addTag("locationId", locationId)
                    .addTag("itemId", itemId)
                    .addField("value", weightKg)
                    .time(Instant.now(), WritePrecision.MS);
            writeApi.writePoint(bucket, influxOrg, point);
        } catch (Exception e) {
            log.error("Failed to write weight to InfluxDB: {}", e.getMessage());
        }
    }

    /**
     * Write environment data — legacy method, now writes as separate measurements.
     */
    public void writeEnvironment(String locationId, double tempC, double humidityPct) {
        writeGeneric("demo-tenant", locationId, "temperature", tempC);
        writeGeneric("demo-tenant", locationId, "humidity", humidityPct);
    }

    // ── Generic Query (works for ANY sensor type) ─────────────────────────

    /**
     * Query history for any sensor type, any tenant, any location.
     */
    public List<Map<String, Object>> queryGenericHistory(String tenantId, String locationId,
                                                          String sensorType, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"%s\") " +
                "|> filter(fn: (r) => r.tenantId == \"%s\") " +
                "|> filter(fn: (r) => r.locationId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, sensorType, tenantId, locationId
        );
        return executeQuery(flux);
    }

    /**
     * Query ALL sensor types for a tenant's location.
     */
    public List<Map<String, Object>> queryAllSensorsForLocation(String tenantId,
                                                                  String locationId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r.tenantId == \"%s\") " +
                "|> filter(fn: (r) => r.locationId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, tenantId, locationId
        );
        return executeQuery(flux);
    }

    /**
     * Query sensor data formatted for the ML service.
     */
    public List<Map<String, Object>> queryForML(String tenantId, String sensorType, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"%s\") " +
                "|> filter(fn: (r) => r.tenantId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 1h, fn: mean, createEmpty: false) " +
                "|> yield(name: \"hourly_mean\")",
                bucket, range, sensorType, tenantId
        );
        return executeQuery(flux);
    }

    // ── Legacy Query Methods (still functional) ──────────────────────────

    public List<Map<String, Object>> queryWeightHistory(String locationId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"weight\") " +
                "|> filter(fn: (r) => r.locationId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, locationId
        );
        return executeQuery(flux);
    }

    public List<Map<String, Object>> queryEnvironmentHistory(String locationId, String range) {
        String flux = String.format(
                "from(bucket: \"%s\") " +
                "|> range(start: -%s) " +
                "|> filter(fn: (r) => r._measurement == \"temperature\" or r._measurement == \"humidity\") " +
                "|> filter(fn: (r) => r.locationId == \"%s\") " +
                "|> filter(fn: (r) => r._field == \"value\") " +
                "|> aggregateWindow(every: 5m, fn: mean, createEmpty: false) " +
                "|> yield(name: \"mean\")",
                bucket, range, locationId
        );
        return executeQuery(flux);
    }

    private List<Map<String, Object>> executeQuery(String flux) {
        List<Map<String, Object>> results = new ArrayList<>();
        try {
            QueryApi queryApi = influxDBClient.getQueryApi();
            List<FluxTable> tables = queryApi.query(flux, influxOrg);
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("time", record.getTime());
                    row.put("measurement", record.getMeasurement());
                    row.put("field", record.getField());
                    row.put("value", record.getValue());
                    if (record.getValueByKey("tenantId") != null) {
                        row.put("tenantId", record.getValueByKey("tenantId"));
                    }
                    if (record.getValueByKey("locationId") != null) {
                        row.put("locationId", record.getValueByKey("locationId"));
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
