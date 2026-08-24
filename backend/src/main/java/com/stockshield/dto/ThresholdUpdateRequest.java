package com.stockshield.dto;

import lombok.*;
import java.util.List;

/**
 * DTO for receiving ML-computed threshold updates from the Python service.
 */
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
public class ThresholdUpdateRequest {

    private List<ThresholdItem> items;

    @Getter @Setter
    @NoArgsConstructor @AllArgsConstructor
    public static class ThresholdItem {
        private String itemId;
        private Double reorderPoint;
        private Double confidence;
        private String model;           // "prophet" or "arima"
        private Integer forecastHorizon; // days
    }
}
