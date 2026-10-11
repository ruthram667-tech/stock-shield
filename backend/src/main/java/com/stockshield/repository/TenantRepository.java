package com.stockshield.repository;

import com.stockshield.model.Tenant;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TenantRepository extends JpaRepository<Tenant, String> {

    List<Tenant> findByIndustry(String industry);
}
