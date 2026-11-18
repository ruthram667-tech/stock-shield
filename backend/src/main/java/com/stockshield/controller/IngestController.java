package com.stockshield.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.stockshield.service.MqttListenerService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * HTTP ingest for devices that POST readings instead of using MQTT (e.g. the ESP32).
 *
 * POST /api/ingest
 * {
 *   "tenantId": "demo-tenant",
 *   "locationId": "shelf-01",
 *   "itemId": "item-001",              // optional, needed for weight
 *   "readings": [
 *     {"sensorType": "temperature", "value": 24.5},
 *     {"sensorType": "humidity",    "value": 55.2},
 *     {"sensorType": "weight",      "value": 12.3}
 *   ]
 * }
 */
@RestController
@RequestMapping("/api/ingest")
@RequiredArgsConstructor
@Slf4j
public class IngestController {

    private final MqttListenerService listener;
    private final ObjectMapper mapper;

    @PostMapping
    public ResponseEntity<Map<String, Object>> ingest(@RequestBody JsonNode body) {
        if (!body.hasNonNull("tenantId") || !body.hasNonNull("locationId")
                || !body.path("readings").isArray()) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "tenantId, locationId and readings[] are required"));
        }

        int accepted = 0;
        for (JsonNode r : body.get("readings")) {
            if (!r.hasNonNull("sensorType") || !r.path("value").isNumber()) {
                continue;
            }
            ObjectNode msg = mapper.createObjectNode();
            msg.put("tenantId", body.get("tenantId").asText());
            msg.put("locationId", body.get("locationId").asText());
            msg.put("sensorType", r.get("sensorType").asText());
            msg.put("value", r.get("value").asDouble());
            if (body.hasNonNull("itemId")) {
                msg.put("itemId", body.get("itemId").asText());
            }
            try {
                listener.ingestGeneric(msg);
                accepted++;
            } catch (Exception e) {
                log.warn("Ingest failed for {}: {}", msg, e.getMessage());
            }
        }
        return ResponseEntity.ok(Map.of("accepted", accepted));
    }
}
