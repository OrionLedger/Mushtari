"""
repo/postgres_repo.py

PostgreSQL implementation of the BaseRepo contract using SQLAlchemy.
Provides a flexible, schema-agnostic interface for interacting with Postgres tables.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from repo.base import BaseRepo
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class PostgresRepository(BaseRepo):
    """
    Concrete implementation of BaseRepo for PostgreSQL.
    Uses SQLAlchemy for connection pooling and SQL generation.
    """

    def __init__(self, connection_uri: Optional[str] = None, **kwargs):
        """
        Initialize the Postgres repository.
        
        Args:
            connection_uri: Full SQLAlchemy connection URI (e.g., postgresql://user:pass@host/db).
            **kwargs: Individual connection params if URI is not provided.
        """
        self.uri = connection_uri or self._build_uri(**kwargs)
        self.engine: Optional[Engine] = None
        self._connected = False

    def _build_uri(self, **kwargs) -> str:
        """Construct a connection URI from individual components."""
        user = kwargs.get("user", "postgres")
        password = kwargs.get("password", "")
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 5432)
        dbname = kwargs.get("dbname", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    # ── Connection Lifecycle ────────────────────────────────────────────

    def connect(self, **kwargs) -> None:
        """Establish connection to PostgreSQL."""
        if self._connected:
            return

        try:
            # Overwrite URI if new one provided in kwargs
            if "connection_uri" in kwargs:
                self.uri = kwargs["connection_uri"]

            self.engine = create_engine(self.uri, pool_pre_ping=True)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self._connected = True
            logger.info(f"Successfully connected to PostgreSQL at {self.engine.url.host}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            raise

    def close(self) -> None:
        """Dispose of the SQLAlchemy engine."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
        self._connected = False
        logger.info("PostgreSQL connection closed.")

    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected

    # ── Read Operations ─────────────────────────────────────────────────

    def get_record(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve records with support for suffix filters (__gte, __lte, etc.).
        """
        if not self._connected:
            self.connect()

        col_str = ", ".join(columns) if columns else "*"
        query_str = f"SELECT {col_str} FROM {table_name}"
        
        where_clause, params = self._build_where_clause(filters)
        if where_clause:
            query_str += f" WHERE {where_clause}"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_str), params)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Query failed on {table_name}: {e}")
            return []

    def get_record_by_id(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by primary key."""
        results = self.get_record(table_name, filters={id_column: record_id})
        return results[0] if results else None

    # ── Write Operations ────────────────────────────────────────────────

    def add_record(self, table_name: str, record: Dict[str, Any]) -> bool:
        """Insert a single record."""
        cols = ", ".join(record.keys())
        placeholders = ", ".join([f":{k}" for k in record.keys()])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

        try:
            with self.engine.connect() as conn:
                conn.execute(text(query), record)
                conn.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Insert failed on {table_name}: {e}")
            return False

    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 500,
    ) -> Dict[str, int]:
        """Perform batch inserts for higher performance."""
        if not records:
            return {"total": 0, "inserted": 0, "failed": 0}

        cols = ", ".join(records[0].keys())
        placeholders = ", ".join([f":{k}" for k in records[0].keys()])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        
        total = len(records)
        inserted = 0
        
        try:
            with self.engine.connect() as conn:
                # Process in chunks
                for i in range(0, total, batch_size):
                    batch = records[i : i + batch_size]
                    conn.execute(text(query), batch)
                    inserted += len(batch)
                conn.commit()
            return {"total": total, "inserted": inserted, "failed": total - inserted}
        except SQLAlchemyError as e:
            logger.error(f"Bulk insert failed on {table_name}: {e}")
            return {"total": total, "inserted": inserted, "failed": total - inserted}

    def update_record(
        self,
        table_name: str,
        record_id: Any,
        updates: Dict[str, Any],
        id_column: str = "id",
    ) -> bool:
        """Update fields for a specific record."""
        set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = :_target_id"
        
        params = {**updates, "_target_id": record_id}

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                conn.commit()
                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Update failed on {table_name}: {e}")
            return False

    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> bool:
        """Delete a record by ID."""
        query = f"DELETE FROM {table_name} WHERE {id_column} = :record_id"
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {"record_id": record_id})
                conn.commit()
                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Delete failed from {table_name}: {e}")
            return False

    # ── Utility ─────────────────────────────────────────────────────────

    def table_exists(self, table_name: str) -> bool:
        """Check for table existence using SQLAlchemy Inspector."""
        if not self._connected:
            self.connect()
        try:
            inspector = inspect(self.engine)
            return inspector.has_table(table_name)
        except Exception as e:
            logger.error(f"Table exists check failed: {e}")
            return False

    def count_records(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records using filters."""
        query_str = f"SELECT COUNT(*) FROM {table_name}"
        where_clause, params = self._build_where_clause(filters)
        if where_clause:
            query_str += f" WHERE {where_clause}"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_str), params)
                return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Count failed on {table_name}: {e}")
            return 0

    # ── Helper ──────────────────────────────────────────────────────────

    def _build_where_clause(self, filters: Optional[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds a SQL WHERE clause and parameter dict from filter suffixes.
        Supports: __gte, __lte, __gt, __lt.
        """
        if not filters:
            return "", {}

        ops = {
            "__gte": ">=",
            "__lte": "<=",
            "__gt": ">",
            "__lt": "<",
        }

        clauses = []
        params = {}

        for key, value in filters.items():
            found_op = False
            for suffix, sql_op in ops.items():
                if key.endswith(suffix):
                    col_name = key[: -len(suffix)]
                    param_name = key.replace("__", "_") # Postgres params can't have __ easily in some drivers
                    clauses.append(f"{col_name} {sql_op} :{param_name}")
                    params[param_name] = value
                    found_op = True
                    break
            
            if not found_op:
                param_name = key
                clauses.append(f"{key} = :{param_name}")
                params[param_name] = value

        return " AND ".join(clauses), params
