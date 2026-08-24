package com.stockshield.repository;

import com.stockshield.model.AlertLog;
import com.stockshield.model.AlertType;
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

    /**
     * Check if an alert of a given type was recently fired for an item (cooldown check).
     */
    boolean existsByItemIdAndAlertTypeAndCreatedAtAfter(String itemId, AlertType alertType, Instant since);
}
