"""
scripts/database/seed_master_data.py

Active seeding script for Phase 2. Uses the DimensionSync ETL flow to 
populate PostgreSQL with an initial high-fidelity product catalog 
and customer base.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from etl.flows.dimension_sync import dimension_sync_flow
from infrastructure.logging.logger import get_logger

logger = get_logger("SeedMasterData")

def seed():
    logger.info("Starting Master Data Seeding (Phase 2)...")

    # 1. CATEGORIES (Already partially seeded by SQL, but can be extended)
    # 2. PRODUCTS
    products_data = [
        {"sku_code": "CER-001", "name": "Traditional Kiln Vase", "category_id": 1, "base_price": 45.0, "status": "active"},
        {"sku_code": "CER-002", "name": "Glazed Dinner Set", "category_id": 1, "base_price": 120.0, "status": "active"},
        {"sku_code": "KIT-101", "name": "Forged Damascus Knife", "category_id": 3, "base_price": 250.0, "status": "active"},
        {"sku_code": "KIT-102", "name": "Cast Iron Skillet", "category_id": 3, "base_price": 85.0, "status": "active"},
        {"sku_code": "DEC-201", "name": "Minimalist Ceramic Lamp", "category_id": 2, "base_price": 75.0, "status": "active"},
    ]
    df_products = pd.DataFrame(products_data)
    
    # 3. CUSTOMERS
    customers_data = [
        {"external_id": "C-1001", "name": "Alice Johnson", "region_id": 1, "segment_id": 2, "acquisition_channel": "Direct"},
        {"external_id": "C-1002", "name": "Bob Smith", "region_id": 2, "segment_id": 1, "acquisition_channel": "Referral"},
        {"external_id": "C-1003", "name": "Charlie Davis", "region_id": 1, "segment_id": 3, "acquisition_channel": "Social"},
    ]
    df_customers = pd.DataFrame(customers_data)

    # We use the generic dimension_sync_flow by passing DataFrames if we wanted,
    # but here we'll just demonstrate loading to Postgres directly using the repo
    # since the flow currently expects a 'source_type' to extract from.
    # Actually, let's just use the PostgresRepository to do a clean bulk insert.
    
    from repo import get_repository
    from etl.config.settings import get_settings
    settings = get_settings().extract.postgres
    
    with get_repository("postgres", **vars(settings)) as repo:
        repo.bulk_insert("products", df_products.to_dict(orient="records"))
        repo.bulk_insert("customers", df_customers.to_dict(orient="records"))
        logger.info("✓ Seed Data injected into PostgreSQL.")

if __name__ == "__main__":
    seed()
