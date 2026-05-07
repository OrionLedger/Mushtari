-- scripts/init_order_schema.sql
-- Migration to support Order-centric Demand Analysis

-- 1. Raw Orders Backlog (Archive)
CREATE TABLE IF NOT EXISTS orders_backlog (
    order_id VARCHAR(255) NOT NULL,
    source_id INTEGER NOT NULL,
    customer_id VARCHAR(255),
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(50),
    total_amount DECIMAL(18, 2),
    raw_items JSONB, -- Nested line items as extracted
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, source_id)
);

-- 2. Exploded Fact Sales (The granular demand records)
CREATE TABLE IF NOT EXISTS fact_sales (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(255) NOT NULL,
    source_id INTEGER NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    quantity DECIMAL(18, 4) NOT NULL,
    unit_price DECIMAL(18, 2) NOT NULL,
    discount DECIMAL(18, 2) DEFAULT 0,
    gross_sale DECIMAL(18, 2) NOT NULL,
    net_sale DECIMAL(18, 2) NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    UNIQUE (order_id, product_id, source_id)
);

-- 3. Customer Dimension
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    segment VARCHAR(100),
    region VARCHAR(100),
    first_order_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Pre-aggregated Daily Demand (UI Performance)
CREATE TABLE IF NOT EXISTS agg_daily_demand (
    product_id VARCHAR(255) NOT NULL,
    sale_date DATE NOT NULL,
    total_qty DECIMAL(18, 4) DEFAULT 0,
    total_revenue DECIMAL(18, 2) DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    PRIMARY KEY (product_id, sale_date)
);

-- 5. Sync Watermarks (Incremental Sync Tracking)
CREATE TABLE IF NOT EXISTS sync_watermarks (
    source_id INTEGER PRIMARY KEY,
    last_synced_at TIMESTAMP NOT NULL,
    last_order_id VARCHAR(255),
    rows_synced INTEGER DEFAULT 0,
    sync_duration_s FLOAT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_date ON fact_sales (product_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales (sale_date);
CREATE INDEX IF NOT EXISTS idx_orders_backlog_source_date ON orders_backlog (source_id, order_date);
CREATE INDEX IF NOT EXISTS idx_agg_daily_product_date ON agg_daily_demand (product_id, sale_date);
