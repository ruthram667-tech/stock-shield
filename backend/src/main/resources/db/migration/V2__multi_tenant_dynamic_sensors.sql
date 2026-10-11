-- ════════════════════════════════════════════════════════════
-- Stock Shield V2 — Multi-Tenant + Dynamic Sensor Types
-- ════════════════════════════════════════════════════════════

-- ── Tenants (multi-tenancy) ──
CREATE TABLE tenants (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    industry    VARCHAR(100),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Dynamic sensor type definitions (per tenant) ──
CREATE TABLE sensor_type_definitions (
    id                  BIGSERIAL PRIMARY KEY,
    tenant_id           VARCHAR(36) NOT NULL REFERENCES tenants(id),
    code                VARCHAR(50) NOT NULL,
    display_name        VARCHAR(100),
    unit                VARCHAR(20),
    category            VARCHAR(50),
    min_safe            DOUBLE PRECISION,
    max_safe            DOUBLE PRECISION,
    critical_min        DOUBLE PRECISION,
    critical_max        DOUBLE PRECISION,
    ml_enabled          BOOLEAN DEFAULT TRUE,
    aggregation_method  VARCHAR(10) DEFAULT 'mean',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_sensor_type_def_tenant ON sensor_type_definitions(tenant_id);

-- ── Extend existing tables with tenant context ──

-- Add tenant_id to inventory_items
ALTER TABLE inventory_items ADD COLUMN tenant_id VARCHAR(36) REFERENCES tenants(id);
-- Rename shelf_id → location_id for generic terminology
ALTER TABLE inventory_items RENAME COLUMN shelf_id TO location_id;

-- Add tenant context to sensors
ALTER TABLE sensors ADD COLUMN tenant_id VARCHAR(36) REFERENCES tenants(id);
ALTER TABLE sensors ADD COLUMN sensor_type_code VARCHAR(50);
ALTER TABLE sensors RENAME COLUMN shelf_id TO location_id;

-- Extend alert_log with tenant and sensor type context
ALTER TABLE alert_log ADD COLUMN tenant_id VARCHAR(36) REFERENCES tenants(id);
ALTER TABLE alert_log ADD COLUMN sensor_type VARCHAR(50);
ALTER TABLE alert_log RENAME COLUMN shelf_id TO location_id;
-- Drop the old enum constraint — we now use VARCHAR for flexible alert types
ALTER TABLE alert_log ALTER COLUMN alert_type TYPE VARCHAR(50);

-- ── Seed: Default demo tenant ──
INSERT INTO tenants (id, name, industry) VALUES
    ('demo-tenant', 'StockShield Demo', 'retail-grocery');

-- ── Seed: Sensor type definitions for demo tenant ──
INSERT INTO sensor_type_definitions (tenant_id, code, display_name, unit, category, min_safe, max_safe, critical_min, critical_max, ml_enabled) VALUES
    ('demo-tenant', 'weight',      'Weight',             'kg',  'inventory',     NULL,   NULL,   NULL,   NULL,   TRUE),
    ('demo-tenant', 'temperature', 'Temperature',        '°C',  'environmental', -25.0,  8.0,    -30.0,  15.0,   TRUE),
    ('demo-tenant', 'humidity',    'Relative Humidity',   '%',   'environmental', 20.0,   80.0,   10.0,   90.0,   TRUE);

-- ── Update existing data with demo tenant ──
UPDATE inventory_items SET tenant_id = 'demo-tenant' WHERE tenant_id IS NULL;
UPDATE sensors SET tenant_id = 'demo-tenant' WHERE tenant_id IS NULL;
UPDATE sensors SET sensor_type_code = sensor_type::text WHERE sensor_type_code IS NULL;
UPDATE alert_log SET tenant_id = 'demo-tenant' WHERE tenant_id IS NULL;
