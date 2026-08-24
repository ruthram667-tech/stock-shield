package com.stockshield.service;

import com.stockshield.dto.ThresholdUpdateRequest;
import com.stockshield.model.InventoryItem;
import com.stockshield.repository.InventoryItemRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Handles ML threshold updates — persists to PostgreSQL and syncs the in-memory status map.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ThresholdService {

    private final InventoryItemRepository itemRepository;
    private final MqttListenerService mqttListenerService;

    /**
     * Processes a batch of threshold updates from the ML service.
     */
    @Transactional
    public int updateThresholds(ThresholdUpdateRequest request) {
        int updated = 0;

        for (ThresholdUpdateRequest.ThresholdItem thresholdItem : request.getItems()) {
            InventoryItem item = itemRepository.findById(thresholdItem.getItemId()).orElse(null);
            if (item == null) {
                log.warn("ML threshold update for unknown item: {}", thresholdItem.getItemId());
                continue;
            }

            double oldReorderPoint = item.getReorderPoint();
            item.setReorderPoint(thresholdItem.getReorderPoint());
            itemRepository.save(item);

            // Sync in-memory map
            mqttListenerService.updateReorderPoint(thresholdItem.getItemId(), thresholdItem.getReorderPoint());

            log.info("🧠 ML threshold update: {} reorder point {} → {} (model: {}, confidence: {:.2f})",
                    thresholdItem.getItemId(),
                    oldReorderPoint,
                    thresholdItem.getReorderPoint(),
                    thresholdItem.getModel(),
                    thresholdItem.getConfidence());
            updated++;
        }

        return updated;
    }
}
