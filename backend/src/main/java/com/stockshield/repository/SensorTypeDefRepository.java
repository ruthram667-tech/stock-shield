package com.stockshield.repository;

import com.stockshield.model.SensorTypeDefinition;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SensorTypeDefRepository extends JpaRepository<SensorTypeDefinition, Long> {

    List<SensorTypeDefinition> findByTenantId(String tenantId);

    Optional<SensorTypeDefinition> findByTenantIdAndCode(String tenantId, String code);

    List<SensorTypeDefinition> findByTenantIdAndMlEnabledTrue(String tenantId);

    List<SensorTypeDefinition> findByTenantIdAndCategory(String tenantId, String category);

    boolean existsByTenantIdAndCode(String tenantId, String code);
}
