package com.stockshield.model;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import lombok.*;

/**
 * In-memory status record for an inventory item.
 * Maintained in a HashMap for O(1) lookup by the MQTT listener.
 * NOT persisted to database — computed from live sensor data.
 *
 * Now supports dynamic sensor readings beyond just temperature/humidity.
 */
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class InventoryStatus {

    private String tenantId;
    private String itemId;
    private String locationId;
    private double currentWeight;
    private double fullWeight;
    private double reorderPoint;
    private double depletionRate;    // kg per hour, computed from recent deltas
    private Instant lastUpdated;
    private StockLevel stockLevel;

    /**
     * Dynamic sensor readings map: sensorType → latest value.
     * Instead of hardcoded temperature/humidity fields, any sensor type
     * can be stored here (e.g., "temperature" → 4.2, "pressure" → 101.3, "ph" → 7.1).
     */
    @Builder.Default
    private Map<String, Double> sensorReadings = new ConcurrentHashMap<>();

    /**
     * Timestamps for each sensor type's last reading.
     */
    @Builder.Default
    private Map<String, Instant> sensorTimestamps = new ConcurrentHashMap<>();

    /**
     * Recalculates status fields based on a new weight reading.
     *
     * @param newWeight the new weight in kg from the load cell
     */
    public void recalculate(double newWeight) {
        Instant now = Instant.now();

        // Calculate depletion rate from weight delta
        if (lastUpdated != null && currentWeight > 0) {
            double dt = (now.toEpochMilli() - lastUpdated.toEpochMilli()) / 3_600_000.0; // hours
            if (dt > 0) {
                double delta = currentWeight - newWeight;
                // Exponential moving average for smoothing
                double instantRate = delta / dt;
                this.depletionRate = 0.7 * this.depletionRate + 0.3 * Math.max(0, instantRate);
            }
        }

        this.currentWeight = newWeight;
        this.lastUpdated = now;
        this.stockLevel = classifyLevel(newWeight, fullWeight);
    }

    /**
     * Updates a dynamic sensor reading (works for any sensor type).
     */
    public void updateSensorReading(String sensorType, double value) {
        if (sensorReadings == null) sensorReadings = new ConcurrentHashMap<>();
        if (sensorTimestamps == null) sensorTimestamps = new ConcurrentHashMap<>();
        sensorReadings.put(sensorType, value);
        sensorTimestamps.put(sensorType, Instant.now());
    }

    /**
     * Gets the latest reading for a sensor type (returns null if not present).
     */
    public Double getSensorReading(String sensorType) {
        if (sensorReadings == null) return null;
        return sensorReadings.get(sensorType);
    }

    // ── Convenience accessors for common types (backward compatibility) ──

    public Double getTemperature() {
        return getSensorReading("temperature");
    }

    public Double getHumidity() {
        return getSensorReading("humidity");
    }

    /**
     * Estimates hours until stock reaches zero at the current depletion rate.
     */
    public double estimatedHoursRemaining() {
        if (depletionRate <= 0) return Double.MAX_VALUE;
        return currentWeight / depletionRate;
    }

    /**
     * Returns true if this item needs restocking (below ML-computed reorder point).
     */
    public boolean needsReorder() {
        return currentWeight <= reorderPoint;
    }

    private static StockLevel classifyLevel(double current, double full) {
        if (full <= 0) return StockLevel.EMPTY;
        double pct = current / full;
        if (pct > 0.8) return StockLevel.FULL;
        if (pct > 0.4) return StockLevel.ADEQUATE;
        if (pct > 0.2) return StockLevel.LOW;
        if (pct > 0.05) return StockLevel.CRITICAL;
        return StockLevel.EMPTY;
    }
}
