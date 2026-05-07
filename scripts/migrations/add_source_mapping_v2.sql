-- scripts/migrations/add_source_mapping.sql
-- Adds support for custom table and column mapping to the Data Sources registry.

ALTER TABLE data_sources 
ADD COLUMN IF NOT EXISTS source_table TEXT,
ADD COLUMN IF NOT EXISTS column_mapping JSONB;

-- Update existing records with default empty mapping if needed
UPDATE data_sources SET column_mapping = '{}' WHERE column_mapping IS NULL;
