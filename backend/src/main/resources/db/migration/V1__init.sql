-- ════════════════════════════════════════════════════════════
-- Stock Shield — Initial Schema Migration
-- ════════════════════════════════════════════════════════════

-- ── Enums ──
CREATE TYPE stock_level AS ENUM ('FULL', 'ADEQUATE', 'LOW', 'CRITICAL', 'EMPTY');
CREATE TYPE sensor_type AS ENUM ('WEIGHT', 'TEMPERATURE', 'HUMIDITY');
CREATE TYPE sensor_status AS ENUM ('ONLINE', 'OFFLINE', 'ERROR');
CREATE TYPE alert_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL');
CREATE TYPE alert_type AS ENUM ('LOW_STOCK', 'TEMP_SPIKE', 'HUMIDITY_OUT_OF_RANGE', 'SENSOR_OFFLINE');

-- ── Users ──
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Vendors ──
CREATE TABLE vendors (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    contact_email   VARCHAR(255),
    contact_phone   VARCHAR(50),
    lead_time_days  INT NOT NULL DEFAULT 3,
    address         TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Inventory Items ──
CREATE TABLE inventory_items (
    id              VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    shelf_id        VARCHAR(50) NOT NULL,
    current_weight  DOUBLE PRECISION NOT NULL DEFAULT 0,
    full_weight     DOUBLE PRECISION NOT NULL,
    reorder_point   DOUBLE PRECISION NOT NULL DEFAULT 0,
    unit            VARCHAR(20) NOT NULL DEFAULT 'kg',
    vendor_id       BIGINT REFERENCES vendors(id),
    zone            VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_inventory_shelf ON inventory_items(shelf_id);
CREATE INDEX idx_inventory_category ON inventory_items(category);

-- ── Sensors ──
CREATE TABLE sensors (
    id              VARCHAR(100) PRIMARY KEY,
    shelf_id        VARCHAR(50) NOT NULL,
    sensor_type     sensor_type NOT NULL,
    last_reading    DOUBLE PRECISION,
    last_seen       TIMESTAMP WITH TIME ZONE,
    status          sensor_status NOT NULL DEFAULT 'OFFLINE',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sensor_shelf ON sensors(shelf_id);

-- ── Alert Log ──
CREATE TABLE alert_log (
    id              BIGSERIAL PRIMARY KEY,
    item_id         VARCHAR(50) REFERENCES inventory_items(id),
    shelf_id        VARCHAR(50) NOT NULL,
    alert_type      alert_type NOT NULL,
    severity        alert_severity NOT NULL,
    message         TEXT NOT NULL,
    current_value   DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by BIGINT REFERENCES users(id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alert_item ON alert_log(item_id);
CREATE INDEX idx_alert_created ON alert_log(created_at DESC);
CREATE INDEX idx_alert_unacknowledged ON alert_log(acknowledged) WHERE acknowledged = FALSE;

-- ── Alert Preferences ──
CREATE TABLE alert_preferences (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    alert_type      alert_type NOT NULL,
    channel         VARCHAR(20) NOT NULL DEFAULT 'EMAIL',
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(user_id, alert_type, channel)
);

-- ── Seed Data: Default admin user ──
INSERT INTO users (username, email, password_hash, role)
VALUES ('admin', 'admin@stockshield.local', '$2a$10$placeholder_hash', 'ADMIN');

-- ── Seed Data: Vendors ──
INSERT INTO vendors (name, contact_email, lead_time_days) VALUES
    ('Fresh Farms Co.', 'orders@freshfarms.co', 2),
    ('Dry Goods Wholesale', 'sales@drygoodswholesale.com', 5),
    ('Arctic Cold Storage', 'supply@arcticcold.com', 3);

-- ── Seed Data: Inventory Items ──
INSERT INTO inventory_items (id, name, category, shelf_id, full_weight, reorder_point, unit, vendor_id, zone) VALUES
    ('item-001', 'Basmati Rice 5kg',         'dry-goods',   'shelf-01', 25.0, 5.0,  'kg', 2, 'dry-storage'),
    ('item-002', 'All-Purpose Flour 2kg',     'dry-goods',   'shelf-02', 20.0, 4.0,  'kg', 2, 'dry-storage'),
    ('item-003', 'Granulated Sugar 1kg',      'dry-goods',   'shelf-03', 15.0, 3.0,  'kg', 2, 'dry-storage'),
    ('item-004', 'Whole Milk 1L',             'dairy',       'shelf-04', 12.0, 3.0,  'kg', 1, 'refrigerated'),
    ('item-005', 'Cheddar Cheese Block',      'dairy',       'shelf-05',  8.0, 2.0,  'kg', 1, 'refrigerated'),
    ('item-006', 'Fresh Chicken Breast',      'meat',        'shelf-06', 10.0, 2.5,  'kg', 1, 'refrigerated'),
    ('item-007', 'Frozen Mixed Vegetables',   'frozen',      'shelf-07', 18.0, 3.5,  'kg', 3, 'frozen'),
    ('item-008', 'Ice Cream Tubs 500ml',      'frozen',      'shelf-08', 14.0, 3.0,  'kg', 3, 'frozen'),
    ('item-009', 'Olive Oil 500ml Bottles',   'condiments',  'shelf-09', 12.0, 2.5,  'kg', 2, 'dry-storage'),
    ('item-010', 'Fresh Orange Juice 1L',     'beverages',   'shelf-10', 16.0, 4.0,  'kg', 1, 'refrigerated'),
    ('item-011', 'Canned Tomatoes 400g',      'canned',      'shelf-11', 20.0, 4.0,  'kg', 2, 'dry-storage'),
    ('item-012', 'Penne Pasta 500g',          'dry-goods',   'shelf-12', 18.0, 3.5,  'kg', 2, 'dry-storage');

-- ── Seed Data: Sensors ──
INSERT INTO sensors (id, shelf_id, sensor_type, status) VALUES
    ('hx711-shelf-01', 'shelf-01', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-02', 'shelf-02', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-03', 'shelf-03', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-04', 'shelf-04', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-05', 'shelf-05', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-06', 'shelf-06', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-07', 'shelf-07', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-08', 'shelf-08', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-09', 'shelf-09', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-10', 'shelf-10', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-11', 'shelf-11', 'WEIGHT', 'ONLINE'),
    ('hx711-shelf-12', 'shelf-12', 'WEIGHT', 'ONLINE'),
    ('dht22-shelf-04', 'shelf-04', 'TEMPERATURE', 'ONLINE'),
    ('dht22-shelf-05', 'shelf-05', 'TEMPERATURE', 'ONLINE'),
    ('dht22-shelf-06', 'shelf-06', 'TEMPERATURE', 'ONLINE'),
    ('dht22-shelf-07', 'shelf-07', 'TEMPERATURE', 'ONLINE'),
    ('dht22-shelf-08', 'shelf-08', 'TEMPERATURE', 'ONLINE'),
    ('dht22-shelf-10', 'shelf-10', 'TEMPERATURE', 'ONLINE');
