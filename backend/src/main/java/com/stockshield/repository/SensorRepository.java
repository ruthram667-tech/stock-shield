package com.stockshield.repository;

import com.stockshield.model.Sensor;
import com.stockshield.model.SensorStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SensorRepository extends JpaRepository<Sensor, String> {

    long countByStatus(SensorStatus status);

    List<Sensor> findByLocationId(String locationId);

    List<Sensor> findByTenantId(String tenantId);

    List<Sensor> findByTenantIdAndSensorTypeCode(String tenantId, String sensorTypeCode);

    long countByTenantIdAndStatus(String tenantId, SensorStatus status);
}
