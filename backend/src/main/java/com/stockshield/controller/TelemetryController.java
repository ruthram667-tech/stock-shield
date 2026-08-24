package com.stockshield.controller;

import com.stockshield.repository.TelemetryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/telemetry")
@RequiredArgsConstructor
public class TelemetryController {

    private final TelemetryRepository telemetryRepository;

    /**
     * Weight history for a shelf — used by Chart.js line charts.
     */
    @GetMapping("/{shelfId}")
    public ResponseEntity<List<Map<String, Object>>> getWeightHistory(
            @PathVariable String shelfId,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(telemetryRepository.queryWeightHistory(shelfId, range));
    }

    /**
     * Temperature/humidity history for a shelf — used by environment charts.
     */
    @GetMapping("/environment/{shelfId}")
    public ResponseEntity<List<Map<String, Object>>> getEnvironmentHistory(
            @PathVariable String shelfId,
            @RequestParam(defaultValue = "24h") String range) {
        return ResponseEntity.ok(telemetryRepository.queryEnvironmentHistory(shelfId, range));
    }
}
