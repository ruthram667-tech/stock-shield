package com.stockshield.dto;

import com.stockshield.model.StockLevel;
import lombok.*;

/**
 * Dashboard summary response DTO.
 */
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class DashboardSummary {
    private int totalItems;
    private int lowStockCount;
    private int criticalStockCount;
    private int activeAlerts;
    private double avgTemperature;
    private double avgHumidity;
    private int sensorsOnline;
    private int sensorsOffline;
}
