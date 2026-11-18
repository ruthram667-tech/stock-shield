-- Simulated shelf used by the dashboard "Simulator" page (keeps simulated data
-- separate from the real ESP32 on shelf-01).
INSERT INTO inventory_items (id, name, category, location_id, current_weight, full_weight, reorder_point, unit, zone, tenant_id) VALUES
    ('sim-item-001', 'Simulated Test Shelf', 'simulation', 'sim-shelf-01', 10.0, 25.0, 5.0, 'kg', 'dry-storage', 'demo-tenant')
ON CONFLICT (id) DO NOTHING;
