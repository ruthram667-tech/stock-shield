package com.stockshield.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.stockshield.model.InventoryItem;
import com.stockshield.model.InventoryStatus;
import com.stockshield.model.Sensor;
import com.stockshield.model.SensorStatus;
import com.stockshield.model.StockLevel;
import com.stockshield.repository.InventoryItemRepository;
import com.stockshield.repository.SensorRepository;
import com.stockshield.repository.TelemetryRepository;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.paho.client.mqttv3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Generic MQTT listener service — handles messages from ANY sensor type
 * for ANY tenant. Routes data to InfluxDB, alerts, and WebSocket.
 *
 * Topic format: stockshield/{tenantId}/{locationId}/{sensorType}
 * Legacy format: stockshield/shelf/{shelfId}/{type} (still supported)
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class MqttListenerService implements MqttCallback {

    private final MqttClient mqttClient;
    private final InventoryItemRepository itemRepository;
    private final SensorRepository sensorRepository;
    private final TelemetryRepository telemetryRepository;
    private final SimpMessagingTemplate messagingTemplate;
    private final ObjectMapper objectMapper;

    @Value("${mqtt.qos:1}")
    private int qos;

    @Value("${mqtt.topics.generic}")
    private String genericTopic;

    @Value("${mqtt.topics.weight}")
    private String weightTopic;

    @Value("${mqtt.topics.environment}")
    private String environmentTopic;

    @Value("${mqtt.topics.status}")
    private String statusTopic;

    /**
     * The in-memory status map — keyed by itemId for O(1) lookups.
     * ConcurrentHashMap for thread safety between MQTT listener and API threads.
     */
    private final ConcurrentHashMap<String, InventoryStatus> statusMap = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        // Pre-populate status map from database
        List<InventoryItem> items = itemRepository.findAll();
        for (InventoryItem item : items) {
            statusMap.put(item.getId(), InventoryStatus.builder()
                    .tenantId(item.getTenantId())
                    .itemId(item.getId())
                    .locationId(item.getLocationId())
                    .currentWeight(item.getCurrentWeight())
                    .fullWeight(item.getFullWeight())
                    .reorderPoint(item.getReorderPoint())
                    .depletionRate(0.0)
                    .lastUpdated(Instant.now())
                    .stockLevel(item.getStockLevel())
                    .sensorReadings(new ConcurrentHashMap<>())
                    .sensorTimestamps(new ConcurrentHashMap<>())
                    .build());
        }
        log.info("📊 Pre-populated status map with {} items", statusMap.size());

        // Subscribe to MQTT topics (both generic and legacy)
        try {
            mqttClient.setCallback(this);
            mqttClient.subscribe(
                    new String[]{genericTopic, weightTopic, environmentTopic, statusTopic},
                    new int[]{qos, qos, qos, 0});
            log.info("📡 Subscribed to MQTT topics: {}, {}, {}, {}",
                    genericTopic, weightTopic, environmentTopic, statusTopic);
        } catch (MqttException e) {
            log.error("Failed to subscribe to MQTT topics", e);
        }
    }

    @PreDestroy
    public void cleanup() {
        try {
            if (mqttClient.isConnected()) {
                mqttClient.disconnect();
            }
        } catch (MqttException e) {
            log.warn("Error disconnecting MQTT client", e);
        }
    }

    // ─── MqttCallback Implementation ────────────────────────────────────────

    @Override
    public void connectionLost(Throwable cause) {
        log.warn("⚠️ MQTT connection lost: {}", cause.getMessage());
    }

    @Override
    public void messageArrived(String topic, MqttMessage message) {
        try {
            String payload = new String(message.getPayload());
            JsonNode json = objectMapper.readTree(payload);

            // Route based on message content (generic format)
            if (json.has("tenantId") && json.has("sensorType")) {
                handleGenericMessage(json);
            }
            // Legacy format routing
            else if (topic.contains("/weight")) {
                handleLegacyWeightMessage(json);
            } else if (topic.contains("/environment")) {
                handleLegacyEnvironmentMessage(json);
            } else if (topic.contains("/status")) {
                handleStatusMessage(json);
            }
        } catch (Exception e) {
            log.error("Error processing MQTT message on topic {}: {}", topic, e.getMessage());
        }
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
        // Not publishing from backend
    }

    // ─── Generic Message Handler (works for ANY sensor type) ────────────────

    private void handleGenericMessage(JsonNode json) {
        String tenantId = json.get("tenantId").asText();
        String locationId = json.get("locationId").asText();
        String sensorType = json.get("sensorType").asText();
        double value = json.get("value").asDouble();

        // 1. Write to InfluxDB
        if ("weight".equals(sensorType) && json.has("itemId")) {
            String itemId = json.get("itemId").asText();
            telemetryRepository.writeWeight(tenantId, locationId, itemId, value);

            // Update in-memory status for weight
            InventoryStatus status = statusMap.get(itemId);
            if (status != null) {
                status.recalculate(value);
                messagingTemplate.convertAndSend("/topic/inventory/" + itemId, status);
            }
        } else {
            telemetryRepository.writeGeneric(tenantId, locationId, sensorType, value);
        }

        // 2. Update sensor readings in status map for matching locations
        statusMap.values().stream()
                .filter(s -> s.getLocationId().equals(locationId)
                        && tenantId.equals(s.getTenantId()))
                .forEach(status -> {
                    status.updateSensorReading(sensorType, value);
                    messagingTemplate.convertAndSend(
                            "/topic/" + tenantId + "/" + locationId + "/" + sensorType,
                            Map.of("sensorType", sensorType, "value", value,
                                   "locationId", locationId, "tenantId", tenantId));
                });

        // 3. Update sensor record in DB
        String sensorId = sensorType + "-" + locationId;
        updateSensor(sensorId, tenantId, locationId, sensorType, value);
    }

    // ─── Legacy Message Handlers (backward compatible) ──────────────────────

    private void handleLegacyWeightMessage(JsonNode json) {
        String locationId = json.get("shelfId").asText();
        String itemId = json.get("itemId").asText();
        double weight = json.get("value").asDouble();

        InventoryStatus status = statusMap.get(itemId);
        if (status != null) {
            status.recalculate(weight);
            messagingTemplate.convertAndSend("/topic/inventory/" + itemId, status);
        } else {
            log.warn("Received weight for unknown item: {}", itemId);
        }

        telemetryRepository.writeWeight(locationId, itemId, weight);
        updateSensor("hx711-" + locationId, "demo-tenant", locationId, "weight", weight);
    }

    private void handleLegacyEnvironmentMessage(JsonNode json) {
        String locationId = json.get("shelfId").asText();
        double temp = json.get("temp").asDouble();
        double humidity = json.get("humidity").asDouble();

        statusMap.values().stream()
                .filter(s -> s.getLocationId().equals(locationId))
                .findFirst()
                .ifPresent(status -> {
                    status.updateSensorReading("temperature", temp);
                    status.updateSensorReading("humidity", humidity);
                    messagingTemplate.convertAndSend("/topic/environment/" + locationId, status);
                });

        telemetryRepository.writeEnvironment(locationId, temp, humidity);
        updateSensor("dht22-" + locationId, "demo-tenant", locationId, "temperature", temp);
    }

    private void handleStatusMessage(JsonNode json) {
        String locationId = json.get("shelfId").asText();
        int battery = json.get("battery").asInt();
        int rssi = json.get("rssi").asInt();
        log.debug("Device status — location: {}, battery: {}%, rssi: {}dBm",
                locationId, battery, rssi);
    }

    private void updateSensor(String sensorId, String tenantId, String locationId,
                               String sensorType, double value) {
        sensorRepository.findById(sensorId).ifPresentOrElse(
                sensor -> {
                    sensor.updateReading(value, Instant.now());
                    sensorRepository.save(sensor);
                },
                () -> {
                    // Auto-register new sensor
                    Sensor sensor = Sensor.builder()
                            .id(sensorId)
                            .tenantId(tenantId)
                            .locationId(locationId)
                            .sensorTypeCode(sensorType)
                            .lastReading(value)
                            .lastSeen(Instant.now())
                            .status(SensorStatus.ONLINE)
                            .build();
                    sensorRepository.save(sensor);
                    log.info("📡 Auto-registered new sensor: {} ({} at {})",
                            sensorId, sensorType, locationId);
                }
        );
    }

    // ─── Public API ─────────────────────────────────────────────────────────

    /**
     * O(1) lookup of current inventory status.
     */
    public InventoryStatus getStatus(String itemId) {
        return statusMap.get(itemId);
    }

    /**
     * Returns all inventory statuses.
     */
    public Collection<InventoryStatus> getAllStatuses() {
        return statusMap.values();
    }

    /**
     * Returns statuses for a specific tenant.
     */
    public Collection<InventoryStatus> getStatusesByTenant(String tenantId) {
        return statusMap.values().stream()
                .filter(s -> tenantId.equals(s.getTenantId()))
                .toList();
    }

    /**
     * Updates the reorder point for an item in the in-memory map.
     * Called when ML service pushes new thresholds.
     */
    public void updateReorderPoint(String itemId, double newReorderPoint) {
        InventoryStatus status = statusMap.get(itemId);
        if (status != null) {
            status.setReorderPoint(newReorderPoint);
            log.info("Updated in-memory reorder point for {}: {}", itemId, newReorderPoint);
        }
    }
}
