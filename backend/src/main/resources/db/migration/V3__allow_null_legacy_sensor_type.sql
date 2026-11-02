-- ════════════════════════════════════════════════════════════
-- Stock Shield V3 — Allow NULL for legacy sensor_type & Seed Tenants
-- ════════════════════════════════════════════════════════════

-- Dynamic sensors use sensor_type_code (e.g. vibration, light, pressure, ph)
-- Make legacy enum sensor_type column nullable for dynamic sensor registration
ALTER TABLE sensors ALTER COLUMN sensor_type DROP NOT NULL;

-- Seed additional tenants from simulator
INSERT INTO tenants (id, name, industry) VALUES
    ('pharma-corp', 'PharmaCorp Global', 'pharmaceutical'),
    ('chem-corp', 'ChemCorp Industries', 'chemical_manufacturing')
ON CONFLICT (id) DO NOTHING;

-- Seed sensor types for pharma-corp
INSERT INTO sensor_type_definitions (tenant_id, code, display_name, unit, category, min_safe, max_safe, critical_min, critical_max, ml_enabled) VALUES
    ('pharma-corp', 'temperature', 'Cold Vault Temp', '°C', 'environmental', 2.0, 8.0, 1.0, 10.0, TRUE),
    ('pharma-corp', 'humidity',    'Cold Vault Humidity', '%', 'environmental', 30.0, 60.0, 20.0, 75.0, TRUE),
    ('pharma-corp', 'vibration',   'Storage Vibration', 'g', 'mechanical', 0.0, 0.2, 0.0, 0.5, TRUE),
    ('pharma-corp', 'light',       'Light Exposure', 'lux', 'environmental', 0.0, 50.0, 0.0, 200.0, TRUE)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- Seed sensor types for chem-corp
INSERT INTO sensor_type_definitions (tenant_id, code, display_name, unit, category, min_safe, max_safe, critical_min, critical_max, ml_enabled) VALUES
    ('chem-corp', 'pressure',    'Reactor Pressure', 'psi', 'mechanical', 35.0, 55.0, 30.0, 65.0, TRUE),
    ('chem-corp', 'ph',          'Acid pH Level', 'pH', 'chemical', 1.8, 2.5, 1.5, 3.0, TRUE),
    ('chem-corp', 'temperature', 'Reactor Temperature', '°C', 'thermal', 55.0, 75.0, 50.0, 85.0, TRUE),
    ('chem-corp', 'gas_level',   'Vapor Concentration', 'ppm', 'environmental', 0.0, 20.0, 0.0, 30.0, TRUE)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- Seed inventory items for pharma-corp and chem-corp locations
INSERT INTO inventory_items (id, name, category, location_id, current_weight, full_weight, reorder_point, unit, zone, tenant_id) VALUES
    ('pharma-vaccine-batch', 'mRNA Vaccine Cold Vault', 'biologics', 'cold-vault-01', 10.0, 10.0, 2.0, 'vials', 'biologics_storage', 'pharma-corp'),
    ('chem-acid-tank', 'Sulfuric Synthesis Tank', 'synthesis', 'reactor-tank-03', 1000.0, 1000.0, 200.0, 'L', 'synthesis_unit', 'chem-corp')
ON CONFLICT (id) DO NOTHING;
