package com.stockshield.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

/**
 * Alert log entity — now tenant-aware with dynamic sensor type context.
 * Stores alerts for any sensor type (not just LOW_STOCK and TEMP_SPIKE).
 */
@Entity
@Table(name = "alert_log")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class AlertLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tenant_id", length = 36)
    private String tenantId;

    @Column(name = "item_id", length = 50)
    private String itemId;

    @Column(name = "location_id", nullable = false, length = 50)
    private String locationId;

    /** Dynamic alert type: "LOW_STOCK", "THRESHOLD_BREACH", "SENSOR_OFFLINE", etc. */
    @Column(name = "alert_type", nullable = false, length = 50)
    private String alertType;

    /** Which sensor type triggered this alert (e.g., "temperature", "pressure") */
    @Column(name = "sensor_type", length = 50)
    private String sensorType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AlertSeverity severity;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String message;

    @Column(name = "current_value")
    private Double currentValue;

    @Column(name = "threshold_value")
    private Double thresholdValue;

    @Column(nullable = false)
    private Boolean acknowledged;

    @Column(name = "acknowledged_by")
    private Long acknowledgedBy;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        if (acknowledged == null) acknowledged = false;
    }
}
