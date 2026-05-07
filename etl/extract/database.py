"""
etl/extract/database.py

Database extractor — generic implementation that works with any BaseRepo.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from repo.base import BaseRepo
from repo import get_repository
from etl.config.settings import get_settings

logger = get_logger(__name__)


class DatabaseExtractor:
    """
    Generic database extractor that uses the BaseRepo abstraction
    to extract data into a pandas DataFrame.
    """

    def __init__(self, repo: Optional[BaseRepo] = None, db_type: str = "cassandra", uri: Optional[str] = None):
        """
        Initialize the extractor.
        
        Args:
            repo:    A pre-configured BaseRepo instance.
            db_type: If repo is None, this type determines which repository to create.
            uri:     Optional URI for database connection.
        """
        if repo is not None:
            self._repo = repo
            return

        settings = get_settings().extract
        if db_type == "cassandra":
            c_settings = settings.cassandra
            self._repo = get_repository(
                "cassandra",
                username=c_settings.username,
                password=c_settings.password,
                contact_points=c_settings.contact_points,
                port=c_settings.port,
            )
            if c_settings.keyspace:
                self._repo.set_keyspace(c_settings.keyspace)
        elif db_type == "postgres":
            import os
            self._repo = get_repository(
                "postgres",
                connection_uri=uri or os.getenv("POSTGRES_URI")
            )
        else:
            raise ValueError(f"Unsupported database type for extraction: {db_type}")

    def validate_connection(self) -> bool:
        """Verify the repository is connected."""
        try:
            if not self._repo.is_connected():
                self._repo.connect()
            return self._repo.is_connected()
        except Exception as exc:
            logger.error(f"Database connection check failed: {exc}")
            return False

    def extract(
        self,
        table_name: str = "Sales",
        columns: Optional[List[str]] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extract records from the database table, applying column mapping if provided.

        Args:
            column_mapping: Dict of {internal_name: source_name}
        """
        mapping = column_mapping or {}
        
        logger.info(
            f"Extracting [{self._repo}] from table={table_name}, product_id={product_id}, "
            f"range=[{start_date} → {end_date}], mapped_fields={len(mapping)}"
        )

        # 1. Prepare filters using source column names
        filters = {}
        if product_id:
            ext_name = mapping.get("product_id", "product_id")
            filters[ext_name] = product_id
        if start_date:
            ext_name = mapping.get("order_date", mapping.get("sell_date", "order_date"))
            filters[f"{ext_name}__gte"] = start_date
        if end_date:
            ext_name = mapping.get("order_date", mapping.get("sell_date", "order_date"))
            filters[f"{ext_name}__lte"] = end_date

        # 2. Extract
        rows = self._repo.get_record(
            table_name=table_name,
            filters=filters,
            columns=columns,
        )

        df = pd.DataFrame(rows)

        # 3. Rename columns handled by exploder in orders mode

        metadata: Dict[str, Any] = {
            "source_type": "database",
            "source_name": f"{self._repo.__class__.__name__}://{table_name}",
            "record_count": len(df),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "product_id": product_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            "mapping_applied": bool(mapping),
        }

        logger.info(f"Extracted {len(df)} records from {table_name}")
        return df, metadata

    def close(self):
        """Release the database connection."""
        try:
            self._repo.close()
        except Exception:
            pass


# ── Prefect task wrapper ────────────────────────────────────────────

@task(
    name="extract-from-database",
    retries=3,
    retry_delay_seconds=10,
    description="Extract data from a database via the internal repository layer.",
)
def extract_from_database(
    table_name: str = "Sales",
    columns: Optional[List[str]] = None,
    product_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    repo: Optional[BaseRepo] = None,
    db_type: str = "cassandra",
    uri: Optional[str] = None,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Prefect task: extract data from the database."""
    extractor = DatabaseExtractor(repo=repo, db_type=db_type, uri=uri)
    try:
        if not extractor.validate_connection():
            extractor._repo.connect()
            
        return extractor.extract(
            table_name=table_name,
            columns=columns,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            column_mapping=column_mapping,
        )
    finally:
        extractor.close()
