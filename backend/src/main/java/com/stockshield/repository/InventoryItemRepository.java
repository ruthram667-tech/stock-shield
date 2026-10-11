package com.stockshield.repository;

import com.stockshield.model.InventoryItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface InventoryItemRepository extends JpaRepository<InventoryItem, String> {

    List<InventoryItem> findByTenantId(String tenantId);

    List<InventoryItem> findByTenantIdAndCategory(String tenantId, String category);

    List<InventoryItem> findByLocationId(String locationId);

    List<InventoryItem> findByTenantIdAndLocationId(String tenantId, String locationId);
}
