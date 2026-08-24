package com.stockshield.service;

import com.stockshield.dto.InventoryItemResponse;
import com.stockshield.model.InventoryItem;
import com.stockshield.model.InventoryStatus;
import com.stockshield.repository.InventoryItemRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Business logic for inventory management — merges DB records with live sensor data.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class InventoryService {

    private final InventoryItemRepository itemRepository;
    private final MqttListenerService mqttListenerService;

    /**
     * Returns all inventory items enriched with live status data.
     */
    public List<InventoryItemResponse> getAllItems() {
        List<InventoryItem> items = itemRepository.findAll();
        List<InventoryItemResponse> responses = new ArrayList<>();

        for (InventoryItem item : items) {
            responses.add(enrichWithLiveData(item));
        }
        return responses;
    }

    /**
     * Returns a single item enriched with live status data.
     */
    public Optional<InventoryItemResponse> getItem(String itemId) {
        return itemRepository.findById(itemId)
                .map(this::enrichWithLiveData);
    }

    /**
     * Returns items currently below their reorder point.
     */
    public List<InventoryItemResponse> getAlertItems() {
        List<InventoryItemResponse> alerts = new ArrayList<>();
        for (InventoryStatus status : mqttListenerService.getAllStatuses()) {
            if (status.needsReorder()) {
                itemRepository.findById(status.getItemId())
                        .map(this::enrichWithLiveData)
                        .ifPresent(alerts::add);
            }
        }
        return alerts;
    }

    /**
     * Merges static DB item with live in-memory status.
     */
    private InventoryItemResponse enrichWithLiveData(InventoryItem item) {
        InventoryStatus status = mqttListenerService.getStatus(item.getId());

        InventoryItemResponse.InventoryItemResponseBuilder builder = InventoryItemResponse.builder()
                .id(item.getId())
                .name(item.getName())
                .category(item.getCategory())
                .shelfId(item.getShelfId())
                .zone(item.getZone())
                .fullWeight(item.getFullWeight())
                .reorderPoint(item.getReorderPoint())
                .unit(item.getUnit());

        if (status != null) {
            builder.currentWeight(status.getCurrentWeight())
                   .stockPercentage(status.getCurrentWeight() / item.getFullWeight())
                   .stockLevel(status.getStockLevel())
                   .depletionRate(status.getDepletionRate())
                   .estimatedHoursRemaining(status.estimatedHoursRemaining())
                   .needsReorder(status.needsReorder())
                   .temperature(status.getTemperature())
                   .humidity(status.getHumidity())
                   .lastUpdated(status.getLastUpdated());
        } else {
            builder.currentWeight(item.getCurrentWeight())
                   .stockPercentage(item.getStockPercentage())
                   .stockLevel(item.getStockLevel())
                   .depletionRate(0)
                   .estimatedHoursRemaining(Double.MAX_VALUE)
                   .needsReorder(item.isLowStock())
                   .lastUpdated(item.getUpdatedAt());
        }

        return builder.build();
    }
}
