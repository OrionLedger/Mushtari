"""
Database loader — writes processed data back to Cassandra, MongoDB, or PostgreSQL
via dynamic configuration and internal abstractions.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from repo.cassandra_repo import CassandraRepository
from etl.config.settings import get_settings

logger = get_logger(__name__)

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
    repo: Optional[Any] = None,
    batch_size: int = 100,
) -> Dict[str, Any]:
    """
    Load a DataFrame into a target database engine.

    Args:
        df:             The DataFrame to load.
        table_name:     Target table or collection.
        db_type:        Target database type: 'cassandra', 'mongo', or 'postgres'.
        connection_uri: Explicit connection string (for Mongo/Postgres). If missing, uses settings.
        repo:           Optional pre-configured Repository instance (mainly for Cassandra).
        batch_size:     Batch logging counter.

    Returns:
        Summary dict with inserted/failed counts.
    """
    total = len(df)
    inserted = 0
    failed = 0

    if total == 0:
        return {"table": table_name, "total": 0, "inserted": 0, "failed": 0, "type": db_type}

    logger.info(f"Loading {total} records into '{table_name}' using {db_type.upper()}")

    if db_type == "postgres":
        inserted, failed = _load_postgres(df, table_name, connection_uri)
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


def _load_cassandra(df: pd.DataFrame, table_name: str, repo: Optional[CassandraRepository], batch_size: int):
    settings = get_settings().extract.cassandra
    own_repo = False
    inserted = 0
    failed = 0

    if repo is None:
        repo = CassandraRepository(
            username=settings.username,
            password=settings.password,
            contact_points=settings.contact_points,
            port=settings.port,
        )
        if hasattr(settings, "keyspace") and settings.keyspace:
            repo.set_keyspace(settings.keyspace)
        own_repo = True

    for idx, row in df.iterrows():
        record = row.to_dict()
        cleaned_record = {}
        for k, v in record.items():
            if pd.isna(v):
                cleaned_record[k] = None
            elif hasattr(v, "item"): 
                cleaned_record[k] = v.item()
            else:
                cleaned_record[k] = v

        try:
            repo.add_sales_record(
                table_name=table_name,
                record=cleaned_record,
            )
            inserted += 1
        except Exception as exc:
            failed += 1
            if failed <= 5:
                logger.warning(f"[LOAD] Cassandra Insert failed — Row {idx}: {exc}")

        if inserted > 0 and inserted % batch_size == 0:
            logger.info(f"[LOAD] Progress: {inserted}/{len(df)} inserted")

    if own_repo:
        try:
            repo.close()
        except:
            pass
            
    return inserted, failed


def _load_mongo(df: pd.DataFrame, collection_name: str, uri: Optional[str]):
    try:
        import pymongo
    except ImportError:
        raise ImportError("pymongo is not installed. Run `pip install pymongo`.")
        
    settings = get_settings()
    # Fallback to a default setting if implicit config block isn't defined explicitly
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


def _load_postgres(df: pd.DataFrame, table_name: str, uri: Optional[str]):
    try:
        from sqlalchemy import create_engine
    except ImportError:
        raise ImportError("SQLAlchemy is not installed. To route to Postgres, run `pip install psycopg2-binary sqlalchemy`.")

    conn_str = uri or "postgresql://user:password@localhost:5432/mushtari"
    engine = create_engine(conn_str)
    
    try:
        # Pandas to_sql natively manages bulk insertions over postgres
        df.to_sql(table_name, engine, if_exists="append", index=False)
        return len(df), 0
    except Exception as e:
        logger.error(f"[LOAD] PostgreSQL table write failed: {e}")
        return 0, len(df)
    finally:
        engine.dispose()
