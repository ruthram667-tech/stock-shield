package com.stockshield.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

/**
 * Represents a product tracked on a shelf.
 * Weight is updated in real-time from HX711 load cell readings.
 */
@Entity
@Table(name = "inventory_items")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class InventoryItem {

    @Id
    @Column(length = 50)
    private String id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, length = 100)
    private String category;

    @Column(name = "shelf_id", nullable = false, length = 50)
    private String shelfId;

    @Column(name = "current_weight", nullable = false)
    private Double currentWeight;

    @Column(name = "full_weight", nullable = false)
    private Double fullWeight;

    @Column(name = "reorder_point", nullable = false)
    private Double reorderPoint;

    @Column(nullable = false, length = 20)
    private String unit;

    @Column(name = "vendor_id")
    private Long vendorId;

    @Column(length = 50)
    private String zone;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at")
    private Instant updatedAt;

    /**
     * Returns stock as a percentage of full weight (0.0 to 1.0).
     */
    public double getStockPercentage() {
        if (fullWeight == null || fullWeight <= 0) return 0.0;
        return Math.min(1.0, Math.max(0.0, currentWeight / fullWeight));
    }

    /**
     * Returns true if current weight is at or below the reorder point.
     */
    public boolean isLowStock() {
        return currentWeight <= reorderPoint;
    }

    /**
     * Classifies current stock level into a discrete category.
     */
    public StockLevel getStockLevel() {
        double pct = getStockPercentage();
        if (pct > 0.8) return StockLevel.FULL;
        if (pct > 0.4) return StockLevel.ADEQUATE;
        if (pct > 0.2) return StockLevel.LOW;
        if (pct > 0.05) return StockLevel.CRITICAL;
        return StockLevel.EMPTY;
    }

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        updatedAt = Instant.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = Instant.now();
    }
}
