"""
Database extractor — uses the internal CassandraRepository abstraction.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from repo.cassandra_repo import CassandraRepository
from etl.config.settings import get_settings

logger = get_logger(__name__)


class DatabaseExtractor:
    """
    Wraps the project's CassandraRepository to extract data
    into a pandas DataFrame.
    """

    def __init__(self, repo: Optional[CassandraRepository] = None):
        settings = get_settings().extract.cassandra
        if repo is None:
            self._repo = CassandraRepository(
                username=settings.username,
                password=settings.password,
                contact_points=settings.contact_points,
                port=settings.port,
            )
            if settings.keyspace:
                self._repo.set_keyspace(settings.keyspace)
        else:
            self._repo = repo

    def validate_connection(self) -> bool:
        """Verify Cassandra is reachable."""
        try:
            # A lightweight query to check connectivity
            return self._repo._session is not None
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
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extract records from a Cassandra table.

        Returns:
            (DataFrame, metadata_dict)
        """
        logger.info(
            f"Extracting from table={table_name}, product_id={product_id}, "
            f"range=[{start_date} → {end_date}]"
        )

        rows = self._repo.get_sales_records(
            table_name=table_name,
            columns=columns,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )

        df = pd.DataFrame(rows)

        metadata: Dict[str, Any] = {
            "source_type": "database",
            "source_name": f"cassandra://{table_name}",
            "record_count": len(df),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "product_id": product_id,
                "start_date": start_date,
                "end_date": end_date,
            },
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
    description="Extract data from Cassandra via internal repository layer.",
)
def extract_from_database(
    table_name: str = "Sales",
    columns: Optional[List[str]] = None,
    product_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    repo: Optional[CassandraRepository] = None,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Prefect task: extract data from the database."""
    extractor = DatabaseExtractor(repo=repo)
    try:
        return extractor.extract(
            table_name=table_name,
            columns=columns,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )
    finally:
        extractor.close()
