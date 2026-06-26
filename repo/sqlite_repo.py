"""
repo/sqlite_repo.py

SQLite implementation of the BaseRepo contract using the built-in sqlite3 module.
Zero external dependencies — works with Python's standard library.

Provides the same interface as PostgresRepository so services can switch
between them without code changes. Supports suffix-based range filtering
(__gte, __lte, __gt, __lt) identical to the Postgres implementation.

The database file is auto-created on first connect if it doesn't exist.
Tables are created lazily via execute_script() — the app can run
init_postgres.sql (SQLite-compatible subset) at startup.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from repo.base import BaseRepo
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SQLiteRepository(BaseRepo):
    """
    Concrete implementation of BaseRepo for SQLite.

    Stores data in a single file. Supports concurrent reads via WAL mode.
    Writes are serialized by SQLite's internal locking.

    Args:
        db_path: Path to the SQLite database file. Defaults to './moshtari.db'.
    """

    # ── Suffix Operators (must match postgres_repo.py) ──────────────────
    _OPS = {
        "__gte": ">=",
        "__lte": "<=",
        "__gt": ">",
        "__lt": "<",
    }

    def __init__(self, db_path: Optional[str] = None, **kwargs):
        """
        Initialize the SQLite repository.

        Args:
            db_path: Path to the .db file. If not provided, uses kwargs['db_path'],
                     then the SQLITE_PATH env var, then defaults to './moshtari.db'.
        """
        if db_path:
            self.db_path = str(db_path)
        else:
            self.db_path = kwargs.get("db_path") or "./moshtari.db"

        self._conn: Optional[sqlite3.Connection] = None
        self._connected = False

    # ── Connection Lifecycle ────────────────────────────────────────────

    def connect(self, **kwargs) -> None:
        """Open or reuse a connection to the SQLite database."""
        if self._connected:
            return

        path = kwargs.get("db_path", self.db_path)
        self.db_path = str(path)

        try:
            # Ensure parent directory exists
            parent = Path(self.db_path).parent
            if parent != Path("."):
                parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,  # FastAPI runs in threadpool
            )
            # Enable WAL mode for concurrent reads
            self._conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys=ON")
            # Row factory for dict-like access
            self._conn.row_factory = sqlite3.Row

            self._connected = True
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            self._connected = False
            raise

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None
        self._connected = False
        logger.info("SQLite connection closed.")

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
        Retrieve records with optional filters and column projection.

        Supports suffix-based range filters: __gte, __lte, __gt, __lt.
        """
        if not self._connected:
            self.connect()

        start = time.perf_counter()
        col_expr = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_expr} FROM {self._quote(table_name)}"

        where_clause, params = self._build_where_clause(filters)
        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            cursor = self._conn.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

            self._log_latency("get_record", table_name, start)
            return rows
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_record({table_name}): {e}")
            return []

    def get_record_by_id(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by primary key column."""
        results = self.get_record(table_name, filters={id_column: record_id})
        return results[0] if results else None

    # ── Write Operations ────────────────────────────────────────────────

    def add_record(self, table_name: str, record: Dict[str, Any]) -> bool:
        """Insert a single record into the table."""
        if not self._connected:
            self.connect()

        cols = ", ".join(self._quote(c) for c in record.keys())
        placeholders = ", ".join(["?" for _ in record])
        values = self._serialize_values(record)
        values_list = list(values.values()) if isinstance(values, dict) else list(values)

        query = f"INSERT INTO {self._quote(table_name)} ({cols}) VALUES ({placeholders})"

        try:
            self._conn.execute(query, values_list)
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"SQLite insert failed on {table_name}: {e}")
            return False

    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 500,
    ) -> Dict[str, int]:
        """
        Insert multiple records efficiently using executemany.

        Args:
            table_name: Target table.
            records: List of record dicts.
            batch_size: Number of rows per chunk.

        Returns:
            Summary dict with total, inserted, failed counts.
        """
        if not records:
            return {"total": 0, "inserted": 0, "failed": 0}
        if not self._connected:
            self.connect()

        cols = ", ".join(self._quote(c) for c in records[0].keys())
        placeholders = ", ".join(["?" for _ in records[0]])
        query = f"INSERT INTO {self._quote(table_name)} ({cols}) VALUES ({placeholders})"

        total = len(records)
        inserted = 0

        try:
            # Serialize all records
            param_sets = []
            for rec in records:
                vals = self._serialize_values(rec)
                param_sets.append(list(vals.values()) if isinstance(vals, dict) else list(vals))

            # Chunk and insert
            for i in range(0, total, batch_size):
                chunk = param_sets[i : i + batch_size]
                self._conn.executemany(query, chunk)
                inserted += len(chunk)

            self._conn.commit()
            return {"total": total, "inserted": inserted, "failed": total - inserted}
        except sqlite3.Error as e:
            logger.error(f"SQLite bulk insert failed on {table_name}: {e}")
            return {"total": total, "inserted": inserted, "failed": total - inserted}

    def update_record(
        self,
        table_name: str,
        record_id: Any,
        updates: Dict[str, Any],
        id_column: str = "id",
    ) -> bool:
        """Update fields on an existing record identified by primary key."""
        if not self._connected:
            self.connect()

        set_clause = ", ".join(f"{self._quote(k)} = ?" for k in updates.keys())
        serialized = self._serialize_values(updates)
        set_values = list(serialized.values()) if isinstance(serialized, dict) else list(serialized)

        query = (
            f"UPDATE {self._quote(table_name)} "
            f"SET {set_clause} "
            f"WHERE {self._quote(id_column)} = ?"
        )

        try:
            cursor = self._conn.execute(query, set_values + [record_id])
            self._conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"SQLite update failed on {table_name}: {e}")
            return False

    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> bool:
        """Delete a record by primary key."""
        if not self._connected:
            self.connect()

        query = f"DELETE FROM {self._quote(table_name)} WHERE {self._quote(id_column)} = ?"
        try:
            cursor = self._conn.execute(query, [record_id])
            self._conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"SQLite delete failed on {table_name}: {e}")
            return False

    # ── Utility ─────────────────────────────────────────────────────────

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the SQLite database."""
        if not self._connected:
            self.connect()
        try:
            cursor = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [table_name],
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"SQLite table check failed: {e}")
            return False

    def count_records(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count records, optionally filtered."""
        query = f"SELECT COUNT(*) FROM {self._quote(table_name)}"
        where_clause, params = self._build_where_clause(filters)
        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            cursor = self._conn.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"SQLite count failed on {table_name}: {e}")
            return 0

    def get_tables(self) -> List[str]:
        """Retrieve all user table names in the database."""
        if not self._connected:
            self.connect()
        try:
            cursor = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"SQLite get_tables failed: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Retrieve column names and types using PRAGMA table_info."""
        if not self._connected:
            self.connect()
        try:
            cursor = self._conn.execute(f"PRAGMA table_info({self._quote(table_name)})")
            return [
                {"name": row[1], "type": row[2]}
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            logger.error(f"SQLite get_table_columns failed for {table_name}: {e}")
            return []

    def execute_script(self, script_content: str) -> bool:
        """
        Execute a multi-statement SQL script.

        Splits on semicolons and executes each statement individually.
        Handles SQLite-compatible DDL and DML.

        Args:
            script_content: The raw SQL script string.

        Returns:
            True if all statements executed, False otherwise.
        """
        if not self._connected:
            self.connect()
        try:
            # Split into individual statements
            statements = [s.strip() for s in script_content.split(";") if s.strip()]
            for stmt in statements:
                # Skip empty or comment-only lines
                if stmt.upper().startswith("CREATE EXTENSION"):
                    continue  # PostgreSQL-specific, skip
                self._conn.execute(stmt)
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"SQLite script execution failed: {e}")
            return False

    # ── Private Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _quote(name: str) -> str:
        """Quote an identifier for safe SQL usage."""
        return f'"{name}"'

    def _build_where_clause(
        self, filters: Optional[Dict[str, Any]]
    ) -> Tuple[str, List[Any]]:
        """
        Build SQL WHERE clause and params list from filter dict.

        Supports suffix filters: __gte, __lte, __gt, __lt.
        Uses ? placeholders for SQLite compatibility.
        """
        if not filters:
            return "", []

        clauses = []
        params = []

        for key, value in filters.items():
            found_op = False
            for suffix, sql_op in self._OPS.items():
                if key.endswith(suffix):
                    col_name = self._quote(key[: -len(suffix)])
                    clauses.append(f"{col_name} {sql_op} ?")
                    params.append(value)
                    found_op = True
                    break

            if not found_op:
                clauses.append(f"{self._quote(key)} = ?")
                params.append(value)

        return " AND ".join(clauses), params

    def _serialize_values(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize Python objects for SQLite storage.

        - dict/list → JSON string
        - UUID → string
        - datetime → ISO format string
        - bytes → blob (stored as-is)
        """
        serialized = {}
        for k, v in record.items():
            if isinstance(v, (dict, list)):
                serialized[k] = json.dumps(v, default=str)
            elif isinstance(v, datetime):
                serialized[k] = v.isoformat()
            elif hasattr(v, "hex") and hasattr(v, "bytes"):  # UUID
                serialized[k] = str(v)
            elif isinstance(v, bytes):
                serialized[k] = v
            elif v is None:
                serialized[k] = None
            else:
                serialized[k] = v
        return serialized

    def _log_latency(self, operation: str, table: str, start_time: float) -> None:
        """Log database operation latency (mimics telemetry from postgres_repo)."""
        duration = time.perf_counter() - start_time
        logger.debug(
            f"sqlite_latency op={operation} table={table} duration_seconds={duration:.4f}"
        )
