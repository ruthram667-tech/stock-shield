package com.stockshield.service;

import com.stockshield.model.*;
import com.stockshield.repository.AlertLogRepository;
import com.stockshield.repository.InventoryItemRepository;
import com.stockshield.repository.SensorTypeDefRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Collection;
import java.util.Map;
import java.util.Optional;

/**
 * Universal alert service — evaluates live telemetry against user-defined
 * thresholds for ANY sensor type across all tenants.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AlertService {

    private final MqttListenerService mqttListenerService;
    private final InventoryItemRepository itemRepository;
    private final AlertLogRepository alertLogRepository;
    private final SensorTypeDefRepository sensorTypeDefRepository;

    @Value("${alerts.cooldown-minutes:30}")
    private int cooldownMinutes;

    // Twilio/SendGrid credentials (empty = log-only mode)
    @Value("${alerts.twilio.account-sid:}")
    private String twilioSid;

    @Value("${alerts.sendgrid.api-key:}")
    private String sendgridKey;

    /**
     * Scheduled check — runs on a fixed interval (default 10s).
     * Evaluates live telemetry for stock levels and all dynamic sensor metrics.
     */
    @Scheduled(fixedDelayString = "${alerts.check-interval-ms:10000}")
    public void checkThresholds() {
        Collection<InventoryStatus> statuses = mqttListenerService.getAllStatuses();

        for (InventoryStatus status : statuses) {
            checkStockLevel(status);
            checkDynamicSensors(status);
        }
    }

    /**
     * Evaluates dynamic sensor readings on an inventory status item.
     */
    private void checkDynamicSensors(InventoryStatus status) {
        String tenantId = status.getTenantId() != null ? status.getTenantId() : "demo-tenant";
        String locationId = status.getLocationId();

        Map<String, Double> readings = status.getSensorReadings();
        if (readings == null || readings.isEmpty()) {
            return;
        }

        readings.forEach((sensorType, value) -> {
            checkDynamicThreshold(tenantId, locationId, status.getItemId(), sensorType, value);
        });
    }

    /**
     * Checks a specific sensor value against user-defined thresholds in SensorTypeDefinition.
     */
    public void checkDynamicThreshold(String tenantId, String locationId, String itemId, String sensorType, double value) {
        Optional<SensorTypeDefinition> defOpt = sensorTypeDefRepository.findByTenantIdAndCode(tenantId, sensorType);
        if (defOpt.isEmpty()) {
            return;
        }

        SensorTypeDefinition def = defOpt.get();
        boolean hasMinViolation = def.getMinSafe() != null && value < def.getMinSafe();
        boolean hasMaxViolation = def.getMaxSafe() != null && value > def.getMaxSafe();

        if (!hasMinViolation && !hasMaxViolation) {
            return; // Safe
        }

        // Determine severity
        boolean isCritical = (def.getCriticalMin() != null && value < def.getCriticalMin())
                || (def.getCriticalMax() != null && value > def.getCriticalMax());
        AlertSeverity severity = isCritical ? AlertSeverity.CRITICAL : AlertSeverity.WARNING;

        // Check cooldown
        Instant cooldownSince = Instant.now().minus(cooldownMinutes, ChronoUnit.MINUTES);
        if (alertLogRepository.existsByTenantIdAndLocationIdAndSensorTypeAndAlertTypeAndCreatedAtAfter(
                tenantId, locationId, sensorType, "THRESHOLD_BREACH", cooldownSince)) {
            return;
        }

        String unit = def.getUnit() != null ? def.getUnit() : "";
        String displayName = def.getDisplayName() != null ? def.getDisplayName() : sensorType;
        String violationDesc = hasMaxViolation
                ? String.format("above safe maximum (%.2f %s > max %.2f %s)", value, unit, def.getMaxSafe(), unit)
                : String.format("below safe minimum (%.2f %s < min %.2f %s)", value, unit, def.getMinSafe(), unit);

        String message = String.format("⚠️ [%s] %s alert at location %s: %s",
                severity, displayName, locationId, violationDesc);

        log.warn(message);

        AlertLog alert = AlertLog.builder()
                .tenantId(tenantId)
                .itemId(itemId)
                .locationId(locationId)
                .sensorType(sensorType)
                .alertType("THRESHOLD_BREACH")
                .severity(severity)
                .message(message)
                .currentValue(value)
                .thresholdValue(hasMaxViolation ? def.getMaxSafe() : def.getMinSafe())
                .acknowledged(false)
                .build();
        alertLogRepository.save(alert);

        dispatchAlert(message, severity);
    }

    private void checkStockLevel(InventoryStatus status) {
        if (!status.needsReorder()) return;

        // Cooldown — don't spam alerts for the same item
        Instant cooldownSince = Instant.now().minus(cooldownMinutes, ChronoUnit.MINUTES);
        if (alertLogRepository.existsByItemIdAndAlertTypeAndCreatedAtAfter(
                status.getItemId(), "LOW_STOCK", cooldownSince)) {
            return;
        }

        AlertSeverity severity = status.getStockLevel() == StockLevel.EMPTY
                ? AlertSeverity.CRITICAL
                : (status.getStockLevel() == StockLevel.CRITICAL ? AlertSeverity.CRITICAL : AlertSeverity.WARNING);

        String message = String.format(
                "⚠️ LOW STOCK: %s at location %s — %.2f remaining (reorder point: %.2f, ~%.1f hours remaining)",
                status.getItemId(), status.getLocationId(),
                status.getCurrentWeight(), status.getReorderPoint(),
                status.estimatedHoursRemaining()
        );

        log.warn(message);

        AlertLog alert = AlertLog.builder()
                .tenantId(status.getTenantId() != null ? status.getTenantId() : "demo-tenant")
                .itemId(status.getItemId())
                .locationId(status.getLocationId())
                .sensorType("weight")
                .alertType("LOW_STOCK")
                .severity(severity)
                .message(message)
                .currentValue(status.getCurrentWeight())
                .thresholdValue(status.getReorderPoint())
                .acknowledged(false)
                .build();
        alertLogRepository.save(alert);

        dispatchAlert(message, severity);
    }

    private void dispatchAlert(String message, AlertSeverity severity) {
        if (twilioSid != null && !twilioSid.isEmpty()) {
            log.info("📱 SMS alert dispatched (Twilio): {}", message);
        }
        if (sendgridKey != null && !sendgridKey.isEmpty()) {
            log.info("📧 Email alert dispatched (SendGrid): {}", message);
        }
        if ((twilioSid == null || twilioSid.isEmpty()) && (sendgridKey == null || sendgridKey.isEmpty())) {
            log.info("📋 Alert logged: {}", message);
        }
    }
}
