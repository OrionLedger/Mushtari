-- OrionLedger / Mushtari: PostgreSQL Initialisation Script
-- Decoupled Relational Dimension Layer for Demand Analysis metadata.

-- 1. EXTENSIONS & SCHEMA
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. IDENTITY & ACCESS MANAGEMENT
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 3. PRODUCT METADATA
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    base_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    unit_cost DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    weight DECIMAL(10, 3), -- kg
    dimensions VARCHAR(100), -- WxHxD
    current_stock INTEGER DEFAULT 0,
    safety_stock INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'retired', 'draft')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. CRM & GEOGRAPHY
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    country_code CHAR(2) NOT NULL,
    currency CHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC'
);

CREATE TABLE IF NOT EXISTS segments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    min_spend DECIMAL(15, 2) DEFAULT 0.00,
    max_spend DECIMAL(15, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(100) UNIQUE, -- Matches External CRM ID or Kafka Source ID
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    region_id INTEGER REFERENCES regions(id),
    segment_id INTEGER REFERENCES segments(id),
    acquisition_channel VARCHAR(50),
    ltv DECIMAL(18, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. AUDIT & LOGGING
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    source_db VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    duration_ms INTEGER,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. AI CONTENT MANAGEMENT
CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    impact VARCHAR(20) CHECK (impact IN ('low', 'moderate', 'high')),
    description TEXT,
    visual_schema JSONB DEFAULT '{}', -- Stores the IRS schema for UI rendering
    product_id INTEGER REFERENCES products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(20) NOT NULL, -- PDF, Excel, CSV
    file_path TEXT NOT NULL,
    author_id UUID REFERENCES users(id),
    file_size_kb INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. INDEXING FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku_code);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_customers_region ON customers(region_id);
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);

-- 10. CONSTRAINTS FOR IDEMPOTENCY
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'categories_name_key') THEN
        ALTER TABLE categories ADD CONSTRAINT categories_name_key UNIQUE (name);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'regions_name_key') THEN
        ALTER TABLE regions ADD CONSTRAINT regions_name_key UNIQUE (name);
    END IF;
END $$;

-- 7. INITIAL SEED DATA
INSERT INTO roles (name, permissions) VALUES 
('Analyst', '{"read_all": true, "run_ml": true, "view_dashboard": true}'),
('Admin', '{"all": true}')
ON CONFLICT (name) DO NOTHING;

INSERT INTO categories (name, description) VALUES 
('Ceramics', 'Clay-based pottery and dinnerware'),
('Decor', 'Interior design objects and ornaments'),
('Kitchenware', 'High-durability kitchen tools')
ON CONFLICT (name) DO NOTHING;

INSERT INTO regions (name, country_code, currency, timezone) VALUES 
('Beirut Central', 'LB', 'LBP', 'Asia/Beirut'),
('Dubai Logistics', 'AE', 'AED', 'Asia/Dubai'),
('Riyadh North', 'SA', 'SAR', 'Asia/Riyadh')
ON CONFLICT (name) DO NOTHING;

INSERT INTO segments (name, description, min_spend) VALUES 
('Wholesale', 'Large volume buyers / Distributors', 5000.00),
('Retail', 'Individual high-frequency buyers', 0.00),
('VIP', 'Loyalty program tier members', 1000.00)
ON CONFLICT (name) DO NOTHING;

-- Insights Seed
INSERT INTO insights (title, category, impact, description, visual_schema) VALUES 
('Global Growth Spike', 'Growth', 'high', 'Sales exceeded Q1 forecast by 18% overall.', '{"type": "area", "primary_metric": "revenue"}'),
('Supply Risk: SKU #102', 'Anomaly', 'moderate', 'Lead time from East Logistics increased by 4 days.', '{"type": "alert", "trigger": "lead_time"}');

-- Reports Seed
INSERT INTO reports (name, report_type, file_path, file_size_kb) VALUES 
('Annual Demand Forecast 2024', 'PDF', '/reports/annual_2024.pdf', 2450),
('Q1 Regional Sales Audit', 'Excel', '/reports/q1_audit.xlsx', 890);
