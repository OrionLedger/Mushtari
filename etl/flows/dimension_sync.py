"""
etl/flows/dimension_sync.py

Specialized ETL flow for synchronizing relational dimension data (Products, Customers)
into PostgreSQL. Unlike the sales fact-store ETL, this flow focuses on relational 
integrity and master-data management.
"""

from typing import Any, Dict, List, Optional, Literal
import pandas as pd
from prefect import flow, task
from infrastructure.logging.logger import get_logger
from etl.flows.etl_flow import dispatch_extract
from etl.load.database import load_to_database
from etl.config.settings import get_settings

logger = get_logger(__name__)

@flow(
    name="dimension-sync-flow",
    description="Synchronize master data dimensions into the PostgreSQL store.",
    log_prints=True,
)
def dimension_sync_flow(
    target_table: Literal["products", "categories", "regions", "segments", "customers"],
    source_type: str = "csv",
    source_config: Optional[Dict[str, Any]] = None,
    db_uri: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronizes a specific dimension table from a source into PostgreSQL.
    """
    source_config = source_config or {}
    results = {"target": target_table, "status": "started"}

    print(f"\n{'='*60}")
    print(f"  Dimension Sync: {target_table.upper()}")
    print(f"{'='*60}")

    # 1. EXTRACT
    print(f"▶ Step 1: Extracting from {source_type}...")
    df, meta = dispatch_extract(source_type, source_config)
    results["extract"] = meta
    
    if df.empty:
        logger.warning(f"No data extracted for {target_table}. Aborting.")
        results["status"] = "skipped"
        return results

    # 2. TRANSFORM (Basic Metadata Cleaning)
    print(f"▶ Step 2: Preparing {len(df)} records...")
    # Fill basic NaNs for text fields
    df = df.where(pd.notnull(df), None)

    # 3. LOAD TO POSTGRES
    print(f"▶ Step 3: Loading to PostgreSQL '{target_table}'...")
    settings = get_settings().extract.postgres
    db_summary = load_to_database(
        df=df,
        table_name=target_table,
        db_type="postgres",
        connection_uri=db_uri or settings.uri,
        batch_size=100
    )
    
    results["load"] = db_summary
    results["status"] = "completed"
    
    print(f"\n✓ Sync completed: {db_summary['inserted']} records persistent.")
    return results

@flow(name="sync-catalog-flow")
def sync_catalog(product_file: str, customer_file: str):
    """Orchestrates the full catalog sync."""
    dimension_sync_flow(target_table="products", source_config={"file_path": product_file})
    dimension_sync_flow(target_table="customers", source_config={"file_path": customer_file})
