-- V8: Set strict temperature (20-25°C) and humidity (40-60%) thresholds for demo-tenant
-- Readings outside safe range trigger WARNING alerts
-- Readings outside critical range trigger CRITICAL alerts

UPDATE sensor_type_definitions
SET min_safe = 20.0, max_safe = 25.0, critical_min = 18.0, critical_max = 27.0
WHERE tenant_id = 'demo-tenant' AND code = 'temperature';

UPDATE sensor_type_definitions
SET min_safe = 40.0, max_safe = 60.0, critical_min = 35.0, critical_max = 65.0
WHERE tenant_id = 'demo-tenant' AND code = 'humidity';
