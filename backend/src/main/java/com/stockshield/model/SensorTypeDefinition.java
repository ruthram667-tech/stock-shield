package com.stockshield.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

/**
 * User-defined sensor type with custom thresholds.
 * Replaces the hardcoded SensorType enum — each tenant defines their own
 * sensor types (temperature, pressure, pH, vibration, etc.) with custom
 * safe ranges that drive the alert engine.
 */
@Entity
@Table(name = "sensor_type_definitions",
       uniqueConstraints = @UniqueConstraint(columnNames = {"tenant_id", "code"}))
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class SensorTypeDefinition {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tenant_id", nullable = false, length = 36)
    private String tenantId;

    /** Machine-readable code: "temperature", "pressure", "ph", "vibration", etc. */
    @Column(nullable = false, length = 50)
    private String code;

    /** Human-readable label: "Temperature (°C)", "Tank Pressure", etc. */
    @Column(name = "display_name", length = 100)
    private String displayName;

    /** Measurement unit: "°C", "PSI", "kg", "pH", "g", etc. */
    @Column(length = 20)
    private String unit;

    /** Logical category: "environmental", "inventory", "chemical", "mechanical" */
    @Column(length = 50)
    private String category;

    // ── Thresholds (user-defined, not hardcoded) ──

    /** Warning if value drops below this */
    @Column(name = "min_safe")
    private Double minSafe;

    /** Warning if value exceeds this */
    @Column(name = "max_safe")
    private Double maxSafe;

    /** Critical alert if value drops below this */
    @Column(name = "critical_min")
    private Double criticalMin;

    /** Critical alert if value exceeds this */
    @Column(name = "critical_max")
    private Double criticalMax;

    /** Whether the ML service should train forecasting models on this metric */
    @Column(name = "ml_enabled")
    private Boolean mlEnabled;

    /** InfluxDB aggregation method: "mean", "max", "min", "sum" */
    @Column(name = "aggregation_method", length = 10)
    private String aggregationMethod;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        if (mlEnabled == null) mlEnabled = true;
        if (aggregationMethod == null) aggregationMethod = "mean";
    }

    /**
     * Checks if a value is within the safe range.
     */
    public boolean isWithinSafeRange(double value) {
        if (minSafe != null && value < minSafe) return false;
        if (maxSafe != null && value > maxSafe) return false;
        return true;
    }

    /**
     * Checks if a value is in the critical zone.
     */
    public boolean isCritical(double value) {
        if (criticalMin != null && value < criticalMin) return true;
        if (criticalMax != null && value > criticalMax) return true;
        return false;
    }
}
