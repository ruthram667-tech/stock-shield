package com.stockshield.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

/**
 * Represents a physical sensor attached to a shelf.
 * Maps to HX711 (weight) or DHT22 (temperature/humidity) hardware.
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

    @Column(name = "shelf_id", nullable = false, length = 50)
    private String shelfId;

    @Enumerated(EnumType.STRING)
    @Column(name = "sensor_type", nullable = false)
    private SensorType sensorType;

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
