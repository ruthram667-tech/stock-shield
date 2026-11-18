package com.stockshield.repository;

import com.stockshield.model.Sensor;
import com.stockshield.model.SensorStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SensorRepository extends JpaRepository<Sensor, String> {

    @Query(value = "SELECT COUNT(*) FROM sensors WHERE status = CAST(:#{#status.name()} AS sensor_status)",
            nativeQuery = true)
    long countByStatus(SensorStatus status);

    List<Sensor> findByLocationId(String locationId);

    List<Sensor> findByTenantId(String tenantId);

    List<Sensor> findByTenantIdAndSensorTypeCode(String tenantId, String sensorTypeCode);

    @Query(value = "SELECT COUNT(*) FROM sensors WHERE tenant_id = :tenantId "
            + "AND status = CAST(:#{#status.name()} AS sensor_status)", nativeQuery = true)
    long countByTenantIdAndStatus(String tenantId, SensorStatus status);
}
