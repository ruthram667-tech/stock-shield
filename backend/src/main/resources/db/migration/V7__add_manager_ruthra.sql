-- V7: Add manager account 'ruthra'
INSERT INTO users
(username, email, password_hash, role, full_name, assigned_location, is_active)
VALUES
('ruthra', 'ruthra@stockshield.local', '1234', 'MANAGER', 'Ruthra', NULL, true)
ON CONFLICT (username) DO NOTHING;
