"""
etl/load/database.py

Database loader — writes processed data back to Cassandra, MongoDB, or PostgreSQL
via dynamic configuration and internal abstractions.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from repo import get_repository
from repo.base import BaseRepo
from etl.config.settings import get_settings

logger = get_logger(__name__)

@task(
    name="load-order-results",
    retries=3,
    description="Multi-table load for order mode (backlog, facts, customers, aggregation).",
)
def load_order_results(
    df_backlog: pd.DataFrame,
    df_sales: pd.DataFrame,
    df_customers: pd.DataFrame,
    db_uri: Optional[str] = None,
    batch_size: int = 200,
) -> Dict[str, Any]:
    """
    Orchestrates the granular load process to multiple relational tables.
    """
    from repo.postgres_repo import PostgresRepository
    import os
    
    uri = db_uri or os.getenv("POSTGRES_URI")
    repo = PostgresRepository(connection_uri=uri)
    
    results = {"inserted": 0, "total": 0, "failed": 0, "tables": {}}
    
    try:
        repo.connect()
        
        # 1. Load Backlog
        if not df_backlog.empty:
            backlog_res = repo.bulk_insert("orders_backlog", _prepare_records(df_backlog), batch_size)
            results["tables"]["orders_backlog"] = backlog_res
            results["inserted"] += backlog_res["inserted"]
            results["total"] += backlog_res["total"]
            
        # 2. Load Sales Facts
        if not df_sales.empty:
            sales_res = repo.bulk_insert("fact_sales", _prepare_records(df_sales), batch_size)
            results["tables"]["fact_sales"] = sales_res
            results["inserted"] += sales_res["inserted"]
            results["total"] += sales_res["total"]
            
        # 3. Load Customers (Upsert needed, but bulk_insert is simple)
        if not df_customers.empty:
            cust_res = repo.bulk_insert("dim_customers", _prepare_records(df_customers), batch_size)
            results["tables"]["dim_customers"] = cust_res
            
        # 4. Load Aggregations
        if not df_sales.empty:
            # product_id, sale_date (DATE part), total_qty, total_rev, order_count
            df_agg = df_sales.copy()
            df_agg['sale_date'] = pd.to_datetime(df_agg['sale_date']).dt.date
            agg = df_agg.groupby(['product_id', 'sale_date']).agg(
                total_qty=('quantity', 'sum'),
                total_revenue=('gross_sale', 'sum'),
                order_count=('order_id', 'nunique')
            ).reset_index()
            agg_res = repo.bulk_insert("agg_daily_demand", _prepare_records(agg), batch_size)
            results["tables"]["agg_daily_demand"] = agg_res
            
        results["status"] = "completed"
        return results
    finally:
        repo.close()


@task(
    name="load-to-database",
    retries=3,
    retry_delay_seconds=10,
    description="Insert processed DataFrame records dynamically into a Cassandra, MongoDB, or PostgreSQL store.",
)
def load_to_database(
    df: pd.DataFrame,
    table_name: str = "processed_sales",
    db_type: str = "cassandra",
    connection_uri: Optional[str] = None,
    repo: Optional[BaseRepo] = None,
    batch_size: int = 100,
) -> Dict[str, Any]:
    """
    Load a DataFrame into a target database engine.
    """
    total = len(df)
    inserted = 0
    failed = 0

    if total == 0:
        return {"table": table_name, "total": 0, "inserted": 0, "failed": 0, "type": db_type}

    logger.info(f"Loading {total} records into '{table_name}' using {db_type.upper()}")

    if db_type == "postgres":
        inserted, failed = _load_postgres(df, table_name, connection_uri, batch_size)
    elif db_type == "mongo":
        inserted, failed = _load_mongo(df, table_name, connection_uri)
    elif db_type == "cassandra":
        inserted, failed = _load_cassandra(df, table_name, repo, batch_size)
    else:
        raise ValueError(f"Unknown database type '{db_type}'. Supported: cassandra, mongo, postgres")

    summary = {
        "table": table_name,
        "type": db_type,
        "total": total,
        "inserted": inserted,
        "failed": failed,
    }

    if failed > 0:
        logger.warning(f"[LOAD] {db_type.upper()} Completed with errors: {inserted} inserted, {failed} failed out of {total}")
    else:
        logger.info(f"[LOAD] {db_type.upper()} Successfully inserted {inserted}/{total} records")

    return summary


def _load_cassandra(df: pd.DataFrame, table_name: str, repo: Optional[BaseRepo], batch_size: int):
    settings = get_settings().extract.cassandra
    own_repo = False

    if repo is None:
        from repo.cassandra_repo import CassandraRepository
        repo = CassandraRepository(
            username=settings.username,
            password=settings.password,
            contact_points=settings.contact_points,
            port=settings.port,
        )
        if hasattr(settings, "keyspace") and settings.keyspace:
            repo.set_keyspace(settings.keyspace)
        own_repo = True

    # Clean DataFrame for Cassandra (remove NaNs, convert numpy types)
    records = _prepare_records(df)

    # Use the new bulk_insert method for efficiency
    try:
        if not repo.is_connected():
            repo.connect()
        result = repo.bulk_insert(
            table_name=table_name,
            records=records,
            batch_size=batch_size
        )
        return result["inserted"], result["failed"]
    finally:
        if own_repo:
            repo.close()


def _load_postgres(df: pd.DataFrame, table_name: str, uri: Optional[str], batch_size: int):
    import os
    from repo.postgres_repo import PostgresRepository
    
    conn_str = uri or os.getenv("POSTGRES_URI")
    repo = PostgresRepository(connection_uri=conn_str)
    
    records = _prepare_records(df)
    
    try:
        repo.connect()
        result = repo.bulk_insert(
            table_name=table_name,
            records=records,
            batch_size=batch_size
        )
        return result["inserted"], result["failed"]
    finally:
        repo.close()


def _load_mongo(df: pd.DataFrame, collection_name: str, uri: Optional[str]):
    try:
        import pymongo
    except ImportError:
        raise ImportError("pymongo is not installed. Run `pip install pymongo`.")
        
    settings = get_settings()
    conn_str = uri or getattr(settings, 'mongo_uri', "mongodb://127.0.0.1:27017")
    
    client = pymongo.MongoClient(conn_str)
    db = client.get_default_database() if client.get_default_database().name else client["mushtari"]
    collection = db[collection_name]
    
    # Clean NaNs out
    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    try:
        res = collection.insert_many(records, ordered=False)
        return len(res.inserted_ids), 0
    except Exception as e:
        logger.error(f"[LOAD] MongoDB bulk insert failed: {e}")
        return 0, len(records)
    finally:
        client.close()


def _prepare_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to a list of dicts with Python primitives."""
    records = []
    for _, row in df.iterrows():
        record = row.to_dict()
        cleaned = {}
        for k, v in record.items():
            if pd.isna(v):
                cleaned[k] = None
            elif hasattr(v, "item"): 
                cleaned[k] = v.item()
            else:
                cleaned[k] = v
        records.append(cleaned)
    return records
