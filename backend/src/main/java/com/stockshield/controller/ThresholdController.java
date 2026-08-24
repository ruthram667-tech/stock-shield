package com.stockshield.controller;

import com.stockshield.dto.ThresholdUpdateRequest;
import com.stockshield.model.InventoryItem;
import com.stockshield.repository.InventoryItemRepository;
import com.stockshield.service.ThresholdService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/thresholds")
@RequiredArgsConstructor
public class ThresholdController {

    private final ThresholdService thresholdService;
    private final InventoryItemRepository itemRepository;

    /**
     * ML service pushes updated reorder points here.
     */
    @PostMapping("/update")
    public ResponseEntity<Map<String, Object>> updateThresholds(
            @RequestBody ThresholdUpdateRequest request) {
        int updated = thresholdService.updateThresholds(request);
        Map<String, Object> response = new HashMap<>();
        response.put("updated", updated);
        response.put("total", request.getItems().size());
        return ResponseEntity.ok(response);
    }

    /**
     * Returns current reorder points for all items.
     */
    @GetMapping
    public ResponseEntity<List<Map<String, Object>>> getThresholds() {
        List<InventoryItem> items = itemRepository.findAll();
        List<Map<String, Object>> thresholds = items.stream()
                .map(item -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("itemId", item.getId());
                    map.put("name", item.getName());
                    map.put("reorderPoint", item.getReorderPoint());
                    map.put("currentWeight", item.getCurrentWeight());
                    map.put("fullWeight", item.getFullWeight());
                    return map;
                })
                .toList();
        return ResponseEntity.ok(thresholds);
    }
}
