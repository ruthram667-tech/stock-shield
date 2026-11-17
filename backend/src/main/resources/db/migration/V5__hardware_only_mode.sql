-- Reset all seeded sensors to OFFLINE until real ESP32 hardware packets arrive
UPDATE sensors SET status = 'OFFLINE', last_reading = NULL, last_seen = NULL;

-- Clear any false startup alerts generated while simulator/seed data was active
TRUNCATE TABLE alert_log RESTART IDENTITY;

-- Ensure demo-tenant temperature/humidity safe thresholds match physical room/cold testing
UPDATE sensor_type_definitions
SET min_safe = 15.0, max_safe = 32.0, critical_min = 10.0, critical_max = 38.0
WHERE tenant_id = 'demo-tenant' AND code = 'temperature';

UPDATE sensor_type_definitions
SET min_safe = 25.0, max_safe = 75.0, critical_min = 15.0, critical_max = 85.0
WHERE tenant_id = 'demo-tenant' AND code = 'humidity';
