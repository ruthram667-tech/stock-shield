package com.stockshield.controller;

import com.stockshield.model.SensorTypeDefinition;
import com.stockshield.repository.SensorTypeDefRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/sensors/types")
@RequiredArgsConstructor
public class SensorTypeController {

    private final SensorTypeDefRepository sensorTypeDefRepository;

    @GetMapping
    public ResponseEntity<List<SensorTypeDefinition>> getSensorTypes(
            @RequestParam(defaultValue = "demo-tenant") String tenantId) {
        return ResponseEntity.ok(sensorTypeDefRepository.findByTenantId(tenantId));
    }

    @GetMapping("/{code}")
    public ResponseEntity<SensorTypeDefinition> getSensorType(
            @PathVariable String code,
            @RequestParam(defaultValue = "demo-tenant") String tenantId) {
        return sensorTypeDefRepository.findByTenantIdAndCode(tenantId, code)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<SensorTypeDefinition> createSensorType(@RequestBody SensorTypeDefinition definition) {
        if (definition.getTenantId() == null || definition.getTenantId().trim().isEmpty()) {
            definition.setTenantId("demo-tenant");
        }
        if (definition.getMlEnabled() == null) {
            definition.setMlEnabled(true);
        }
        if (definition.getAggregationMethod() == null) {
            definition.setAggregationMethod("mean");
        }
        SensorTypeDefinition saved = sensorTypeDefRepository.save(definition);
        return ResponseEntity.ok(saved);
    }

    @PutMapping("/{id}")
    public ResponseEntity<SensorTypeDefinition> updateSensorType(
            @PathVariable Long id,
            @RequestBody SensorTypeDefinition updated) {
        return sensorTypeDefRepository.findById(id)
                .map(existing -> {
                    if (updated.getDisplayName() != null) existing.setDisplayName(updated.getDisplayName());
                    if (updated.getUnit() != null) existing.setUnit(updated.getUnit());
                    if (updated.getCategory() != null) existing.setCategory(updated.getCategory());
                    if (updated.getMinSafe() != null) existing.setMinSafe(updated.getMinSafe());
                    if (updated.getMaxSafe() != null) existing.setMaxSafe(updated.getMaxSafe());
                    if (updated.getCriticalMin() != null) existing.setCriticalMin(updated.getCriticalMin());
                    if (updated.getCriticalMax() != null) existing.setCriticalMax(updated.getCriticalMax());
                    if (updated.getMlEnabled() != null) existing.setMlEnabled(updated.getMlEnabled());
                    if (updated.getAggregationMethod() != null) existing.setAggregationMethod(updated.getAggregationMethod());
                    return ResponseEntity.ok(sensorTypeDefRepository.save(existing));
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteSensorType(@PathVariable Long id) {
        if (sensorTypeDefRepository.existsById(id)) {
            sensorTypeDefRepository.deleteById(id);
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.notFound().build();
    }
}
