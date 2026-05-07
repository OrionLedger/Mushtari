"""
scripts/database/provision_test_db.py

Admin utility to provision an isolated testing database (mushtari_test).
Initializes the schema and seeds it with testing-specific catalog data.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from etl.config.settings import get_settings
from repo import get_repository
from infrastructure.logging.logger import get_logger

logger = get_logger("ProvisionTestDB")

def provision():
    settings = get_settings().extract.postgres
    
    # 1. Create the database (requires non-transactional connection to 'postgres' system db)
    # We use a raw engine with autocommit to bypass the SELECT 1 / transaction logic
    admin_uri = f"postgresql://{settings.user}:{settings.password}@{settings.host}:{settings.port}/postgres"
    engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")
    
    logger.info("Connecting to PostgreSQL Admin...")
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE DATABASE mushtari_test;"))
            logger.info("✓ Created database 'mushtari_test'.")
        except Exception as e:
            if "already exists" in str(e):
                logger.warning("! Database 'mushtari_test' already exists. Re-initializing schema.")
            else:
                logger.error(f"Failed to create test DB: {e}")
                return

    # 2. Deploy Schema to the new test DB
    test_db_settings = vars(settings).copy()
    test_db_settings['dbname'] = 'mushtari_test'
    
    logger.info("Switching to 'mushtari_test' for schema deployment...")
    schema_path = Path("scripts/database/init_postgres.sql")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Use the Repo to execute the full script
    with get_repository("postgres", **test_db_settings) as repo:
        repo.execute_script(schema_sql)
        logger.info("✓ Schema successfully deployed to 'mushtari_test'.")

    # 3. Seed Testing Data
    # For testing, we provide a clean, known catalog
    logger.info("Seeding known test catalog...")
    with get_repository("postgres", **test_db_settings) as repo:
        test_products = [
            {"sku_code": "TEST-01", "name": "Standard Test Unit", "base_price": 10.0, "unit_cost": 5.0, "current_stock": 50, "safety_stock": 10},
            {"sku_code": "TEST-02", "name": "High Value Test Unit", "base_price": 500.0, "unit_cost": 250.0, "current_stock": 5, "safety_stock": 15},
        ]
        repo.bulk_insert("products", test_products)
        logger.info("✓ Test seed data injected.")

    print(f"\n{'='*60}")
    print(f"  TEST DATABASE READY: mushtari_test")
    print(f"  Update your .env to POSTGRES_DB=mushtari_test to run tests.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    provision()
