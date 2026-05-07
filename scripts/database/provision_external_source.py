"""
scripts/database/provision_external_source.py

Provisioning script for Phase 4 ETL Testing. 
Creates an isolated 'external_source_db' with a schema representing 
a legacy ERP or 3rd-party sales system.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import uuid
import time
import random

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from etl.config.settings import get_settings
from repo import get_repository
from infrastructure.logging.logger import get_logger

logger = get_logger("ProvisionExternalSource")

def provision():
    settings = get_settings().extract.postgres
    admin_uri = f"postgresql://{settings.user}:{settings.password}@{settings.host}:{settings.port}/postgres"
    engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")
    
    # 1. Create DB
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE DATABASE external_source_db;"))
            logger.info("✓ Created database 'external_source_db'.")
        except Exception as e:
            if "already exists" in str(e):
                logger.warning("! Database 'external_source_db' already exists.")
            else:
                logger.error(f"Failed: {e}")
                return

    # 2. Deploy Legacy Schema (Aligned with target for simple test)
    source_settings = vars(settings).copy()
    source_settings['dbname'] = 'external_source_db'
    
    legacy_schema = """
    CREATE TABLE IF NOT EXISTS legacy_sales (
        id SERIAL PRIMARY KEY,
        product_id INTEGER,
        quantity DECIMAL,
        price_at_sale DECIMAL,
        ds TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_identifier VARCHAR(50) DEFAULT 'ERP_v1'
    );
    """
    with get_repository("postgres", **source_settings) as repo:
        repo.execute_script(legacy_schema)
        
        # 3. Seed with enough data to pass validation (>10 rows)
        logger.info("Seeding legacy sales records...")
        sales_records = []
        for _ in range(50):
            sales_records.append({
                "product_id": random.choice([1, 101, 102]),
                "quantity": round(random.uniform(5.0, 25.0), 2),
                "price_at_sale": round(random.uniform(15.0, 150.0), 2),
                "source_identifier": "ERP_Legacy"
            })
        repo.bulk_insert("legacy_sales", sales_records)
        logger.info(f"✓ Seeded {len(sales_records)} legacy sales.")

if __name__ == "__main__":
    provision()
