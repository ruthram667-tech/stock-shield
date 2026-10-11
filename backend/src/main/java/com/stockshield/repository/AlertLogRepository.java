package com.stockshield.repository;

import com.stockshield.model.AlertLog;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface AlertLogRepository extends JpaRepository<AlertLog, Long> {

    List<AlertLog> findByAcknowledgedFalseOrderByCreatedAtDesc();

    List<AlertLog> findByItemIdOrderByCreatedAtDesc(String itemId);

    List<AlertLog> findByCreatedAtAfterOrderByCreatedAtDesc(Instant since);

    List<AlertLog> findAllByOrderByCreatedAtDesc(Pageable pageable);

    long countByAcknowledgedFalse();

    // ── Tenant-aware queries ──

    List<AlertLog> findByTenantIdOrderByCreatedAtDesc(String tenantId, Pageable pageable);

    long countByTenantIdAndAcknowledgedFalse(String tenantId);

    /**
     * Cooldown check: has an alert of this type been fired recently for this location + sensor?
     */
    boolean existsByTenantIdAndLocationIdAndSensorTypeAndAlertTypeAndCreatedAtAfter(
            String tenantId, String locationId, String sensorType, String alertType, Instant since);

    /**
     * Legacy cooldown check (kept for backward compatibility).
     */
    boolean existsByItemIdAndAlertTypeAndCreatedAtAfter(String itemId, String alertType, Instant since);
}
