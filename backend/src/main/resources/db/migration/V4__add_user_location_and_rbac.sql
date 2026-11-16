-- ════════════════════════════════════════════════════════════
-- Stock Shield V4 — Role-Based Access Control & Location Scoping
-- ════════════════════════════════════════════════════════════

-- 1. Extend users table for RBAC and Zone Scoping
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(150);
ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_location VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 2. Seed / Update Default Manager (Global access to all facility logs & employee creation)
INSERT INTO users (username, email, password_hash, role, full_name, assigned_location, is_active)
VALUES 
    ('admin', 'admin@stockshield.local', 'admin123', 'MANAGER', 'Chief Facility Manager', NULL, TRUE)
ON CONFLICT (username) DO UPDATE 
SET role = 'MANAGER', 
    full_name = 'Chief Facility Manager',
    password_hash = 'admin123',
    assigned_location = NULL,
    is_active = TRUE;

-- 3. Seed Default Employees with Zone-Restricted Permissions
-- Employee locked to 'frozen' (Cold Storage Freezer)
INSERT INTO users (username, email, password_hash, role, full_name, assigned_location, is_active)
VALUES 
    ('cold_emp', 'cold.storage@stockshield.local', 'cold123', 'EMPLOYEE', 'David Vance (Cold Storage)', 'frozen', TRUE)
ON CONFLICT (username) DO UPDATE 
SET role = 'EMPLOYEE',
    full_name = 'David Vance (Cold Storage)',
    password_hash = 'cold123',
    assigned_location = 'frozen',
    is_active = TRUE;

-- Employee locked to 'dry-storage' (Ambient Dry Goods Racks)
INSERT INTO users (username, email, password_hash, role, full_name, assigned_location, is_active)
VALUES 
    ('dry_emp', 'dry.storage@stockshield.local', 'dry123', 'EMPLOYEE', 'Elena Rostova (Dry Racks)', 'dry-storage', TRUE)
ON CONFLICT (username) DO UPDATE 
SET role = 'EMPLOYEE',
    full_name = 'Elena Rostova (Dry Racks)',
    password_hash = 'dry123',
    assigned_location = 'dry-storage',
    is_active = TRUE;

-- Employee locked to 'refrigerated' (Chilled Dairy & Meat Zone)
INSERT INTO users (username, email, password_hash, role, full_name, assigned_location, is_active)
VALUES 
    ('chilled_emp', 'chilled.ops@stockshield.local', 'chilled123', 'EMPLOYEE', 'Karan Patel (Chilled Logistics)', 'refrigerated', TRUE)
ON CONFLICT (username) DO UPDATE 
SET role = 'EMPLOYEE',
    full_name = 'Karan Patel (Chilled Logistics)',
    password_hash = 'chilled123',
    assigned_location = 'refrigerated',
    is_active = TRUE;
