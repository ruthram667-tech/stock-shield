package com.stockshield.controller;

import com.stockshield.dto.DashboardSummary;
import com.stockshield.model.*;
import com.stockshield.repository.AlertLogRepository;
import com.stockshield.repository.SensorRepository;
import com.stockshield.service.MqttListenerService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Collection;
import java.util.List;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final MqttListenerService mqttListenerService;
    private final AlertLogRepository alertLogRepository;
    private final SensorRepository sensorRepository;

    /**
     * Aggregated summary for dashboard cards, optionally filtered by tenant.
     */
    @GetMapping("/summary")
    public ResponseEntity<DashboardSummary> getSummary(
            @RequestParam(required = false) String tenantId) {
        Collection<InventoryStatus> statuses = (tenantId != null && !tenantId.isBlank())
                ? mqttListenerService.getStatusesByTenant(tenantId)
                : mqttListenerService.getAllStatuses();

        int totalItems = statuses.size();
        int lowStock = 0;
        int critical = 0;
        double tempSum = 0;
        int tempCount = 0;
        double humiditySum = 0;
        int humidityCount = 0;

        for (InventoryStatus s : statuses) {
            if (s.getStockLevel() == StockLevel.LOW || s.getStockLevel() == StockLevel.CRITICAL || s.getStockLevel() == StockLevel.EMPTY) {
                lowStock++;
            }
            if (s.getStockLevel() == StockLevel.CRITICAL || s.getStockLevel() == StockLevel.EMPTY) {
                critical++;
            }
            if (s.getTemperature() != null) {
                tempSum += s.getTemperature();
                tempCount++;
            }
            if (s.getHumidity() != null) {
                humiditySum += s.getHumidity();
                humidityCount++;
            }
        }

        long activeAlerts = (tenantId != null && !tenantId.isBlank())
                ? alertLogRepository.countByTenantIdAndAcknowledgedFalse(tenantId)
                : alertLogRepository.countByAcknowledgedFalse();

        long sensorsOnline = sensorRepository.countByStatus(SensorStatus.ONLINE);
        long sensorsOffline = sensorRepository.countByStatus(SensorStatus.OFFLINE);

        DashboardSummary summary = DashboardSummary.builder()
                .totalItems(totalItems)
                .lowStockCount(lowStock)
                .criticalStockCount(critical)
                .activeAlerts((int) activeAlerts)
                .avgTemperature(tempCount > 0 ? tempSum / tempCount : 0)
                .avgHumidity(humidityCount > 0 ? humiditySum / humidityCount : 0)
                .sensorsOnline((int) sensorsOnline)
                .sensorsOffline((int) sensorsOffline)
                .build();

        return ResponseEntity.ok(summary);
    }

    /**
     * Recent alerts for the dashboard feed, optionally filtered by tenant.
     */
    @GetMapping("/alerts/recent")
    public ResponseEntity<List<AlertLog>> getRecentAlerts(
            @RequestParam(required = false) String tenantId,
            @RequestParam(defaultValue = "20") int limit) {
        if (tenantId != null && !tenantId.isBlank()) {
            return ResponseEntity.ok(
                    alertLogRepository.findByTenantIdOrderByCreatedAtDesc(tenantId, PageRequest.of(0, limit)));
        }
        return ResponseEntity.ok(
                alertLogRepository.findAllByOrderByCreatedAtDesc(PageRequest.of(0, limit)));
    }
}
