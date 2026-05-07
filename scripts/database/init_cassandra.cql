-- OrionLedger / Mushtari: Cassandra (CQL) Initialisation Script
-- High-throughput Fact Store and Inference Logs

-- 1. KEYSPACE CREATION
CREATE KEYSPACE IF NOT EXISTS mushtari 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE mushtari;

-- 2. SALES FACT TABLE (Optimized for Product Temporal Queries)
CREATE TABLE IF NOT EXISTS sales (
    product_id int,
    ds timestamp,
    transaction_id uuid,
    quantity decimal,
    price_at_sale decimal,
    customer_id uuid,
    region_id int,
    channel varchar,
    PRIMARY KEY ((product_id), ds, transaction_id)
) WITH CLUSTERING ORDER BY (ds DESC, transaction_id ASC);

-- 3. INFERENCE LOGS (Audit Trail for AI Predictions)
CREATE TABLE IF NOT EXISTS inference_logs (
    product_id int,
    model_name varchar,
    model_version varchar,
    prediction_ts timestamp,
    features_json text, -- JSON representation of inputs
    predicted_value decimal,
    actual_value decimal, -- Updated post-hoc
    status varchar, -- 'completed', 'drift_detected'
    PRIMARY KEY ((product_id), prediction_ts)
) WITH CLUSTERING ORDER BY (prediction_ts DESC);

-- 4. METRIC CACHE (Pre-aggregated BI Snapshot)
CREATE TABLE IF NOT EXISTS metric_cache (
    metric_name varchar,
    bucket_ds timestamp, -- Hourly/Daily bucket
    value decimal,
    metadata_json text,
    PRIMARY KEY ((metric_name), bucket_ds)
) WITH CLUSTERING ORDER BY (bucket_ds DESC);

-- 5. SYSTEM ALERTS (Immutable Alert Ledger)
CREATE TABLE IF NOT EXISTS system_alerts (
    alert_id uuid,
    severity varchar, -- 'critical', 'warning', 'info'
    event_type varchar,
    alert_ts timestamp,
    message text,
    is_resolved boolean,
    PRIMARY KEY ((severity), alert_ts, alert_id)
) WITH CLUSTERING ORDER BY (alert_ts DESC, alert_id ASC);

-- 6. SAMPLE SEED DATA (For Demonstration)
-- Sales Data
INSERT INTO sales (product_id, ds, transaction_id, quantity, price_at_sale, channel) 
VALUES (1, '2024-04-17 10:00:00', now(), 12.0, 15.50, 'Retail');
INSERT INTO sales (product_id, ds, transaction_id, quantity, price_at_sale, channel) 
VALUES (102, '2024-04-17 11:30:00', now(), 5.0, 45.00, 'Wholesale');

-- Inference Logs
INSERT INTO inference_logs (product_id, model_name, model_version, prediction_ts, predicted_value, status)
VALUES (1, 'XGBoost_Sales_v1', '1.2.0', '2024-04-17 08:00:00', 14.5, 'completed');

-- System Alerts
INSERT INTO system_alerts (alert_id, severity, event_type, alert_ts, message, is_resolved)
VALUES (uuid(), 'critical', 'Inventory_Shortage', '2024-04-17 15:45:00', 'SKU #102 is below safety threshold (5 units remaining).', false);
