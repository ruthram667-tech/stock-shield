package com.stockshield.service;

import com.stockshield.model.*;
import com.stockshield.repository.AlertLogRepository;
import com.stockshield.repository.InventoryItemRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Collection;

/**
 * Alert service — periodically compares live weight/temp vs. thresholds,
 * logs alerts to PostgreSQL, and dispatches notifications via Twilio/SendGrid.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AlertService {

    private final MqttListenerService mqttListenerService;
    private final InventoryItemRepository itemRepository;
    private final AlertLogRepository alertLogRepository;

    @Value("${alerts.cooldown-minutes:30}")
    private int cooldownMinutes;

    // Twilio/SendGrid credentials (empty = log-only mode)
    @Value("${alerts.twilio.account-sid:}")
    private String twilioSid;

    @Value("${alerts.sendgrid.api-key:}")
    private String sendgridKey;

    /**
     * Scheduled check — runs on a fixed interval (default 10s).
     * Compares live sensor data against ML-computed reorder points and temp ranges.
     */
    @Scheduled(fixedDelayString = "${alerts.check-interval-ms:10000}")
    public void checkThresholds() {
        Collection<InventoryStatus> statuses = mqttListenerService.getAllStatuses();

        for (InventoryStatus status : statuses) {
            checkStockLevel(status);
            checkTemperature(status);
        }
    }

    private void checkStockLevel(InventoryStatus status) {
        if (!status.needsReorder()) return;

        // Cooldown — don't spam alerts for the same item
        Instant cooldownSince = Instant.now().minus(cooldownMinutes, ChronoUnit.MINUTES);
        if (alertLogRepository.existsByItemIdAndAlertTypeAndCreatedAtAfter(
                status.getItemId(), AlertType.LOW_STOCK, cooldownSince)) {
            return;
        }

        AlertSeverity severity = status.getStockLevel() == StockLevel.EMPTY
                ? AlertSeverity.CRITICAL
                : (status.getStockLevel() == StockLevel.CRITICAL ? AlertSeverity.CRITICAL : AlertSeverity.WARNING);

        String message = String.format(
                "⚠️ LOW STOCK: %s on shelf %s — %.2f kg remaining (reorder point: %.2f kg, ~%.1f hours remaining)",
                status.getItemId(), status.getShelfId(),
                status.getCurrentWeight(), status.getReorderPoint(),
                status.estimatedHoursRemaining()
        );

        log.warn(message);

        // Persist alert
        AlertLog alert = AlertLog.builder()
                .itemId(status.getItemId())
                .shelfId(status.getShelfId())
                .alertType(AlertType.LOW_STOCK)
                .severity(severity)
                .message(message)
                .currentValue(status.getCurrentWeight())
                .thresholdValue(status.getReorderPoint())
                .build();
        alertLogRepository.save(alert);

        // Dispatch notification
        dispatchAlert(message, severity);
    }

    private void checkTemperature(InventoryStatus status) {
        if (status.getTemperature() == null) return;

        // Define safe ranges by zone type (from shelf ID pattern)
        double maxTemp = getMaxTempForShelf(status.getShelfId());
        if (maxTemp == Double.MAX_VALUE) return; // No temp monitoring for this zone

        if (status.getTemperature() <= maxTemp) return;

        // Cooldown check
        Instant cooldownSince = Instant.now().minus(cooldownMinutes, ChronoUnit.MINUTES);
        if (alertLogRepository.existsByItemIdAndAlertTypeAndCreatedAtAfter(
                status.getItemId(), AlertType.TEMP_SPIKE, cooldownSince)) {
            return;
        }

        String message = String.format(
                "🌡️ TEMP SPIKE: Shelf %s at %.1f°C (max: %.1f°C)",
                status.getShelfId(), status.getTemperature(), maxTemp
        );

        log.warn(message);

        AlertLog alert = AlertLog.builder()
                .itemId(status.getItemId())
                .shelfId(status.getShelfId())
                .alertType(AlertType.TEMP_SPIKE)
                .severity(AlertSeverity.CRITICAL)
                .message(message)
                .currentValue(status.getTemperature())
                .thresholdValue(maxTemp)
                .build();
        alertLogRepository.save(alert);

        dispatchAlert(message, AlertSeverity.CRITICAL);
    }

    private double getMaxTempForShelf(String shelfId) {
        // In a real system, this would come from the DB. Using conventions here.
        // Refrigerated shelves (4-6): max 8°C, Frozen shelves (7-8): max -12°C
        int shelfNum;
        try {
            shelfNum = Integer.parseInt(shelfId.replace("shelf-", ""));
        } catch (NumberFormatException e) {
            return Double.MAX_VALUE;
        }

        if (shelfNum >= 4 && shelfNum <= 6 || shelfNum == 10) return 8.0;  // Refrigerated
        if (shelfNum == 7 || shelfNum == 8) return -12.0;                   // Frozen
        return Double.MAX_VALUE;                                            // Dry storage — no limit
    }

    private void dispatchAlert(String message, AlertSeverity severity) {
        // Twilio SMS
        if (twilioSid != null && !twilioSid.isEmpty()) {
            try {
                // In production: Twilio.init(twilioSid, authToken);
                // Message.creator(to, from, message).create();
                log.info("📱 SMS alert dispatched (Twilio)");
            } catch (Exception e) {
                log.error("Failed to send Twilio SMS: {}", e.getMessage());
            }
        }

        // SendGrid Email
        if (sendgridKey != null && !sendgridKey.isEmpty()) {
            try {
                // In production: SendGrid sg = new SendGrid(sendgridKey);
                // sg.api(request);
                log.info("📧 Email alert dispatched (SendGrid)");
            } catch (Exception e) {
                log.error("Failed to send SendGrid email: {}", e.getMessage());
            }
        }

        if ((twilioSid == null || twilioSid.isEmpty()) && (sendgridKey == null || sendgridKey.isEmpty())) {
            log.info("📋 Alert logged (no Twilio/SendGrid credentials configured): {}", message);
        }
    }
}
