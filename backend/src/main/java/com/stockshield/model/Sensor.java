package com.stockshield.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

/**
 * Represents a physical sensor device at a location.
 * Now supports any sensor type via tenant-defined sensor_type_code
 * instead of the old hardcoded SensorType enum.
 */
@Entity
@Table(name = "sensors")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class Sensor {

    @Id
    @Column(length = 100)
    private String id;

    @Column(name = "tenant_id", length = 36)
    private String tenantId;

    @Column(name = "location_id", nullable = false, length = 50)
    private String locationId;

    /** Dynamic sensor type code — references sensor_type_definitions.code */
    @Column(name = "sensor_type_code", length = 50)
    private String sensorTypeCode;

    @Column(name = "last_reading")
    private Double lastReading;

    @Column(name = "last_seen")
    private Instant lastSeen;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SensorStatus status;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    /**
     * Updates the sensor with a new reading value and marks it as ONLINE.
     */
    public void updateReading(double value, Instant timestamp) {
        this.lastReading = value;
        this.lastSeen = timestamp;
        this.status = SensorStatus.ONLINE;
    }

    /**
     * Returns true if the sensor hasn't reported in over 5 minutes.
     */
    public boolean isStale() {
        if (lastSeen == null) return true;
        return Instant.now().minusSeconds(300).isAfter(lastSeen);
    }

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        if (status == null) status = SensorStatus.OFFLINE;
    }
}
