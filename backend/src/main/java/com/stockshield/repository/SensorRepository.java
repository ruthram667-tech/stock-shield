package com.stockshield.repository;

import com.stockshield.model.Sensor;
import com.stockshield.model.SensorStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SensorRepository extends JpaRepository<Sensor, String> {

    List<Sensor> findByShelfId(String shelfId);

    List<Sensor> findByStatus(SensorStatus status);

    long countByStatus(SensorStatus status);
}
