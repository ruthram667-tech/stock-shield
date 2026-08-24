package com.stockshield.dto;

import com.stockshield.model.StockLevel;
import lombok.*;

import java.time.Instant;

/**
 * Combined inventory item + live status response DTO.
 */
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class InventoryItemResponse {
    private String id;
    private String name;
    private String category;
    private String shelfId;
    private String zone;
    private double currentWeight;
    private double fullWeight;
    private double reorderPoint;
    private String unit;
    private double stockPercentage;
    private StockLevel stockLevel;
    private double depletionRate;
    private double estimatedHoursRemaining;
    private boolean needsReorder;
    private Double temperature;
    private Double humidity;
    private Instant lastUpdated;
}
