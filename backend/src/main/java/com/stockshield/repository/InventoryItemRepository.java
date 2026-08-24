package com.stockshield.repository;

import com.stockshield.model.InventoryItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface InventoryItemRepository extends JpaRepository<InventoryItem, String> {

    Optional<InventoryItem> findByShelfId(String shelfId);

    List<InventoryItem> findByCategory(String category);

    List<InventoryItem> findByZone(String zone);

    @Query("SELECT i FROM InventoryItem i WHERE i.currentWeight <= i.reorderPoint")
    List<InventoryItem> findLowStockItems();

    @Query("SELECT i FROM InventoryItem i WHERE i.currentWeight <= i.fullWeight * 0.05")
    List<InventoryItem> findEmptyItems();
}
