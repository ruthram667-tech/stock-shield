package com.stockshield.controller;

import com.stockshield.repository.TelemetryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Telemetry controller — now supports generic sensor type queries
 * alongside legacy weight/environment endpoints.
 */
@RestController
@RequestMapping("/api/telemetry")
@RequiredArgsConstructor
public class TelemetryController {

    private final TelemetryRepository telemetryRepository;

    // ── Generic Endpoints (any sensor type) ──────────────────────────────

    /**
     * Query history for any sensor type at any location.
     */
    @GetMapping("/{tenantId}/{locationId}/{sensorType}")
    public ResponseEntity<List<Map<String, Object>>> getGenericHistory(
            @PathVariable String tenantId,
            @PathVariable String locationId,
            @PathVariable String sensorType,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(
                telemetryRepository.queryGenericHistory(tenantId, locationId, sensorType, range));
    }

    /**
     * Query ALL sensor types for a location.
     */
    @GetMapping("/{tenantId}/{locationId}")
    public ResponseEntity<List<Map<String, Object>>> getAllSensorsForLocation(
            @PathVariable String tenantId,
            @PathVariable String locationId,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(
                telemetryRepository.queryAllSensorsForLocation(tenantId, locationId, range));
    }

    // ── Legacy Endpoints (backward compatible) ──────────────────────────

    /**
     * Weight history for a location — used by Chart.js line charts.
     */
    @GetMapping("/weight/{locationId}")
    public ResponseEntity<List<Map<String, Object>>> getWeightHistory(
            @PathVariable String locationId,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(telemetryRepository.queryWeightHistory(locationId, range));
    }

    /**
     * Temperature/humidity history for a location — used by environment charts.
     */
    @GetMapping("/environment/{locationId}")
    public ResponseEntity<List<Map<String, Object>>> getEnvironmentHistory(
            @PathVariable String locationId,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(telemetryRepository.queryEnvironmentHistory(locationId, range));
    }
}
