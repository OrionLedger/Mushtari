"""
scripts/database/migrate_sources_table.py

Creates the data_sources registry table in the active Postgres DB.
Safe to run multiple times (idempotent).
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[2]))

from etl.config.settings import get_settings

settings = get_settings().extract.postgres
uri = f"postgresql://{settings.user}:{settings.password}@{settings.host}:{settings.port}/{settings.dbname}"
engine = create_engine(uri)

DDL = """
CREATE TABLE IF NOT EXISTS data_sources (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    source_type VARCHAR(50)  NOT NULL DEFAULT 'Database',
    conn_uri    TEXT         NOT NULL,
    status      VARCHAR(20)  DEFAULT 'active',
    last_synced TIMESTAMP WITH TIME ZONE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.connect() as conn:
    conn.execute(text(DDL))
    conn.commit()

print("data_sources table ready.")
