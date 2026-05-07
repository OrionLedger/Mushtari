"""
scripts/testing/test_etl_db_source.py

Phase 4 Integration Test: Database-to-Database ETL.
Extracts sales from 'external_source_db' and loads them into 
the system's 'mushtari_test' and Cassandra layers.
"""

import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from etl.flows.etl_flow import etl_pipeline_flow
from etl.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger("ETL_DB_Test")

# Environment overrides for the test
# Point Postgres loader URI to our test DB
POSTGRES_TEST_URI = "postgresql://postgres:root@localhost:5432/mushtari_test"
os.environ["POSTGRES_URI"] = POSTGRES_TEST_URI

# Source connection URI
SOURCE_URI = "postgresql://postgres:root@localhost:5432/external_source_db"

def run_test():
    logger.info("Initializing ETL Database Source Test...")
    
    # Run the ETL Flow
    # 1. Source: external_source_db.legacy_sales
    # 2. Target: Postgres mushtari_test (for master record audit)
    # 3. Target: Cassandra mushtari.sales (for fact verification)
    
    result_pg = etl_pipeline_flow(
        source_type="database",
        source_config={
            "table_name": "legacy_sales",
            "db_type": "postgres",
            "uri": SOURCE_URI
        },
        # Load processed results into our relational test store
        load_to_db=True,
        db_type="postgres",
        db_uri=POSTGRES_TEST_URI,
        db_table_name="processed_sales_audit", # Log processed results here
        track_in_mlflow=False
    )
    
    logger.info(f"Relational Load Status: {result_pg.get('status')}")

    # Now run for Cassandra Fact Store
    # In a unified run we'd target multiple, but here we demonstrate the portability
    result_cas = etl_pipeline_flow(
        source_type="database",
        source_config={
            "table_name": "legacy_sales",
            "db_type": "postgres",
            "uri": SOURCE_URI
        },
        load_to_db=True,
        db_type="cassandra",
        db_table_name="sales", # Primary fact table
        track_in_mlflow=False
    )
    
    logger.info(f"Cassandra Load Status: {result_cas.get('status')}")
    
    print(f"\n{'='*60}")
    print(f"  ETL SOURCE TEST COMPLETE")
    print(f"  - Extracted from: external_source_db.legacy_sales")
    print(f"  - Loaded into: mushtari_test (Relational) & Cassandra (Fact)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_test()
