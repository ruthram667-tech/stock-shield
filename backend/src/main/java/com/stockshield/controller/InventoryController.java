package com.stockshield.controller;

import com.stockshield.dto.InventoryItemResponse;
import com.stockshield.service.InventoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/inventory")
@RequiredArgsConstructor
public class InventoryController {

    private final InventoryService inventoryService;

    @GetMapping
    public ResponseEntity<List<InventoryItemResponse>> getAllItems() {
        return ResponseEntity.ok(inventoryService.getAllItems());
    }

    @GetMapping("/{id}")
    public ResponseEntity<InventoryItemResponse> getItem(@PathVariable String id) {
        return inventoryService.getItem(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/alerts")
    public ResponseEntity<List<InventoryItemResponse>> getAlertItems() {
        return ResponseEntity.ok(inventoryService.getAlertItems());
    }
}
