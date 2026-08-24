package com.stockshield.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.stockshield.model.InventoryItem;
import com.stockshield.model.InventoryStatus;
import com.stockshield.model.Sensor;
import com.stockshield.model.SensorType;
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
 * Core MQTT listener service — runs in its own thread, subscribes to
 * sensor topics, and maintains an in-memory HashMap for O(1) status lookups.
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
                    .itemId(item.getId())
                    .shelfId(item.getShelfId())
                    .currentWeight(item.getCurrentWeight())
                    .fullWeight(item.getFullWeight())
                    .reorderPoint(item.getReorderPoint())
                    .depletionRate(0.0)
                    .lastUpdated(Instant.now())
                    .stockLevel(item.getStockLevel())
                    .build());
        }
        log.info("📊 Pre-populated status map with {} items", statusMap.size());

        // Subscribe to MQTT topics
        try {
            mqttClient.setCallback(this);
            mqttClient.subscribe(new String[]{weightTopic, environmentTopic, statusTopic},
                                 new int[]{qos, qos, 0});
            log.info("📡 Subscribed to MQTT topics: {}, {}, {}", weightTopic, environmentTopic, statusTopic);
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

            if (topic.contains("/weight")) {
                handleWeightMessage(json);
            } else if (topic.contains("/environment")) {
                handleEnvironmentMessage(json);
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

    // ─── Message Handlers ───────────────────────────────────────────────────

    private void handleWeightMessage(JsonNode json) {
        String shelfId = json.get("shelfId").asText();
        String itemId = json.get("itemId").asText();
        double weight = json.get("value").asDouble();

        // Update in-memory status
        InventoryStatus status = statusMap.get(itemId);
        if (status != null) {
            status.recalculate(weight);

            // Push real-time update to WebSocket subscribers
            messagingTemplate.convertAndSend("/topic/inventory/" + itemId, status);
        } else {
            log.warn("Received weight for unknown item: {}", itemId);
        }

        // Write to InfluxDB (async — offloaded from callback)
        telemetryRepository.writeWeight(shelfId, itemId, weight);

        // Update sensor status
        updateSensor("hx711-" + shelfId, shelfId, SensorType.WEIGHT, weight);
    }

    private void handleEnvironmentMessage(JsonNode json) {
        String shelfId = json.get("shelfId").asText();
        double temp = json.get("temp").asDouble();
        double humidity = json.get("humidity").asDouble();

        // Find the item on this shelf and update environment
        statusMap.values().stream()
                .filter(s -> s.getShelfId().equals(shelfId))
                .findFirst()
                .ifPresent(status -> {
                    status.updateEnvironment(temp, humidity);
                    messagingTemplate.convertAndSend("/topic/environment/" + shelfId, status);
                });

        // Write to InfluxDB
        telemetryRepository.writeEnvironment(shelfId, temp, humidity);

        // Update sensor
        updateSensor("dht22-" + shelfId, shelfId, SensorType.TEMPERATURE, temp);
    }

    private void handleStatusMessage(JsonNode json) {
        String shelfId = json.get("shelfId").asText();
        int battery = json.get("battery").asInt();
        int rssi = json.get("rssi").asInt();
        log.debug("Device status — shelf: {}, battery: {}%, rssi: {}dBm", shelfId, battery, rssi);
    }

    private void updateSensor(String sensorId, String shelfId, SensorType type, double value) {
        sensorRepository.findById(sensorId).ifPresent(sensor -> {
            sensor.updateReading(value, Instant.now());
            sensorRepository.save(sensor);
        });
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
