"""
repo/postgres_repo.py

PostgreSQL implementation of the BaseRepo contract using SQLAlchemy.
Provides a flexible, schema-agnostic interface for interacting with Postgres tables.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import time

from repo.base import BaseRepo
from infrastructure.logging.logger import get_logger
from infrastructure.monitoring.telemetry import log_database_latency

logger = get_logger(__name__)


class PostgresRepository(BaseRepo):
    """
    Concrete implementation of BaseRepo for PostgreSQL.
    Uses SQLAlchemy for connection pooling and SQL generation.
    """

    def __init__(self, connection_uri: Optional[str] = None, **kwargs):
        """
        Initialize the Postgres repository. Defaults to settings from environment variables.
        """
        from etl.config.settings import get_settings
        settings = get_settings().extract.postgres

        # High-priority: explicit URI
        self.uri = connection_uri or settings.uri
        
        # If still no URI, build from individual components (priority: kwargs > settings)
        if not self.uri:
            user = kwargs.get("user") or settings.user
            password = kwargs.get("password") or settings.password
            host = kwargs.get("host") or settings.host
            port = kwargs.get("port") or settings.port
            dbname = kwargs.get("dbname") or settings.dbname
            self.uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

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

            self.engine = create_engine(
                self.uri, 
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30
            )
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
        if not self._connected:
            self.connect()

        start = time.perf_counter()
        query = f"SELECT {', '.join(columns) if columns else '*'} FROM {table_name}"
        if filters:
            # Simple WHERE clause construction
            where_clauses = [f"{k} = :{k}" for k in filters.keys()]
            query += f" WHERE {' AND '.join(where_clauses)}"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), filters or {})
                data = [dict(row._mapping) for row in result]
                
                # Phase 4 Telemetry
                log_database_latency("get_record", table_name, time.perf_counter() - start, "postgres")
                
                return data
        except SQLAlchemyError as e:
            logger.error(f"Error fetching from {table_name}: {e}")
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
        if not self._connected:
            self.connect()
        cols = ", ".join(record.keys())
        placeholders = ", ".join([f":{k}" for k in record.keys()])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

        try:
            # Serialize dictionaries and lists for JSONB columns if using raw SQL
            import json
            serialized_record = {}
            for k, v in record.items():
                if isinstance(v, (dict, list)):
                    serialized_record[k] = json.dumps(v)
                else:
                    serialized_record[k] = v

            with self.engine.connect() as conn:
                conn.execute(text(query), serialized_record)
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
        if not self._connected:
            self.connect()

        cols = ", ".join(records[0].keys())
        placeholders = ", ".join([f":{k}" for k in records[0].keys()])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        
        total = len(records)
        inserted = 0
        
        try:
            import json
            # Serialize for batch
            processed_records = []
            for r in records:
                processed_row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        processed_row[k] = json.dumps(v)
                    else:
                        processed_row[k] = v
                processed_records.append(processed_row)

            with self.engine.connect() as conn:
                # Process in chunks
                for i in range(0, total, batch_size):
                    batch = processed_records[i : i + batch_size]
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
        if not self._connected:
            self.connect()
        set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = :_target_id"
        
        params = {"_target_id": record_id}
        import json
        for k, v in updates.items():
            if isinstance(v, (dict, list)):
                params[k] = json.dumps(v)
            else:
                params[k] = v

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                conn.commit()
                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Update failed on {table_name}: {e}")
            return False

    def update_records(
        self,
        table_name: str,
        filters: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> int:
        """Update fields for all records matching the filters."""
        if not self._connected:
            self.connect()
        set_clause = ", ".join([f"{k} = :set_{k}" for k in updates.keys()])
        where_clause = " AND ".join([f"{k} = :filter_{k}" for k in filters.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        params = {}
        import json
        for k, v in updates.items():
            params[f"set_{k}"] = json.dumps(v) if isinstance(v, (dict, list)) else v
        for k, v in filters.items():
            params[f"filter_{k}"] = v

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                conn.commit()
                return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Bulk update failed on {table_name}: {e}")
            return 0

    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> bool:
        """Delete a record by ID."""
        if not self._connected:
            self.connect()
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

    def get_tables(self) -> List[str]:
        """Retrieve all physical table names in the connected database."""
        if not self._connected:
            self.connect()
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Retrieve column names and types using SQLAlchemy inspector."""
        if not self._connected:
            self.connect()
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            return [
                {"name": col["name"], "type": str(col["type"])}
                for col in columns
            ]
        except Exception as e:
            logger.error(f"Failed to get columns for {table_name}: {e}")
            return []

    def execute_script(self, script_content: str) -> bool:
        """
        Executes a raw multi-statement SQL script as a single call.
        This handles complex blocks (DO, BEGIN/END) correctly.
        """
        if not self._connected:
            self.connect()
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(script_content))
                conn.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Script execution failed: {e}")
            return False

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
