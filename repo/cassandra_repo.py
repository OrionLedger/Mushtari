"""
repo/cassandra_repo.py

Cassandra implementation of the BaseRepo interface.
Provides high-performance data access to Apache Cassandra partitions
using the Datastax Python Driver.
"""

from typing import Any, Dict, List, Optional
from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement, BatchStatement, BatchType
import logging

from .base import BaseRepo

logger = logging.getLogger(__name__)

class CassandraRepository(BaseRepo):
    """
    Concrete implementation of BaseRepo for Apache Cassandra.
    
    This class wraps the Datastax Cassandra driver to provide a standard
    interface for interacting with Cassandra tables while fulfilling the
    BaseRepo contract.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        contact_points: Optional[List[str]] = None,
        port: Optional[int] = None,
        keyspace: Optional[str] = None
    ) -> None:
        """
        Initialize the repository. Defaults to settings from environment variables.
        """
        from etl.config.settings import get_settings
        settings = get_settings().extract.cassandra

        self._cluster: Optional[Cluster] = None
        self._session: Optional[Session] = None
        
        # Use provided args or fall back to global settings
        username = username or settings.username
        password = password or settings.password
        contact_points = contact_points or settings.contact_points
        port = port or settings.port
        keyspace = keyspace or settings.keyspace

        self._keyspace: Optional[str] = keyspace
        
        self._conn_args = {
            "username": username,
            "password": password,
            "contact_points": contact_points,
            "port": port,
            "keyspace": keyspace
        }
        
        # Initial connection attempt
        try:
            self.connect(**self._conn_args)
        except Exception as e:
            logger.warning(f"Initial connection attempt in __init__ failed: {e}")

    # ── Connection Lifecycle ────────────────────────────────────────────

    def connect(self, **kwargs) -> None:
        """
        Establish a connection to the Cassandra cluster.
        """
        # Merge kwargs with defaults/init params
        args = {**self._conn_args, **kwargs}
        
        contact_points = args.get("contact_points", ["127.0.0.1"])
        port = args.get("port", 9042)
        username = args.get("username")
        password = args.get("password")
        keyspace = args.get("keyspace")

        auth_provider = None
        if username and password:
            auth_provider = PlainTextAuthProvider(username=username, password=password)

        try:
            # Close existing if any
            if self._cluster:
                self.close()

            self._cluster = Cluster(
                contact_points=contact_points,
                port=port,
                auth_provider=auth_provider
            )
            self._session = self._cluster.connect(keyspace)
            self._keyspace = keyspace
            logger.info(f"Connected to Cassandra cluster at {contact_points}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {str(e)}")
            raise

    def close(self) -> None:
        """Gracefully shutdown the cluster and session."""
        if self._cluster:
            try:
                self._cluster.shutdown()
            except Exception as e:
                logger.error(f"Error during cluster shutdown: {e}")
            finally:
                self._cluster = None
                self._session = None
                logger.info("Cassandra repository connection closed.")

    def is_connected(self) -> bool:
        """Determine if the repository has an active session."""
        return self._session is not None and not self._cluster.is_shutdown

    # ── Read Operations ─────────────────────────────────────────────────

    def get_record(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve records using attribute-value equality filters.
        Supports range filters if keys are like 'col__gte', 'col__lte'.
        """
        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {table_name}"
        params = []

        if filters:
            where_clauses = []
            for k, v in filters.items():
                if "__gte" in k:
                    col = k.replace("__gte", "")
                    where_clauses.append(f"{col} >= %s")
                elif "__lte" in k:
                    col = k.replace("__lte", "")
                    where_clauses.append(f"{col} <= %s")
                elif "__gt" in k:
                    col = k.replace("__gt", "")
                    where_clauses.append(f"{col} > %s")
                elif "__lt" in k:
                    col = k.replace("__lt", "")
                    where_clauses.append(f"{col} < %s")
                else:
                    where_clauses.append(f"{k} = %s")
                params.append(v)
            
            query += " WHERE " + " AND ".join(where_clauses)
            query += " ALLOW FILTERING"

        stmt = SimpleStatement(query)
        try:
            if not self._session:
                self.connect()
            rows = self._session.execute(stmt, params)
            return [dict(row._asdict()) for row in rows]
        except Exception as e:
            logger.error(f"Query failed: {query} | Error: {e}")
            return []

    def get_record_by_id(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        results = self.get_record(table_name, filters={id_column: record_id})
        return results[0] if results else None

    # ── Write Operations ────────────────────────────────────────────────

    def add_record(
        self,
        table_name: str,
        record: Dict[str, Any],
    ) -> bool:
        cols = ", ".join(record.keys())
        placeholders = ", ".join(["%s"] * len(record))
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        
        try:
            if not self._session:
                self.connect()
            self._session.execute(query, list(record.values()))
            return True
        except Exception as e:
            logger.error(f"Failed to insert record into {table_name}: {e}")
            return False

    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, int]:
        total = len(records)
        inserted = 0
        failed = 0

        if not self._session:
            self.connect()

        for i in range(0, total, batch_size):
            chunk = records[i : i + batch_size]
            batch = BatchStatement(batch_type=BatchType.UNLOGGED)
            
            for rec in chunk:
                cols = ", ".join(rec.keys())
                placeholders = ", ".join(["%s"] * len(rec))
                query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
                batch.add(SimpleStatement(query), list(rec.values()))
            
            try:
                self._session.execute(batch)
                inserted += len(chunk)
            except Exception as e:
                logger.error(f"Bulk insert failed at offset {i}: {e}")
                failed += len(chunk)

        return {"total": total, "inserted": inserted, "failed": failed}

    def update_record(
        self,
        table_name: str,
        record_id: Any,
        updates: Dict[str, Any],
        id_column: str = "id",
    ) -> bool:
        set_clauses = [f"{k} = %s" for k in updates.keys()]
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {id_column} = %s"
        params = list(updates.values()) + [record_id]
        
        try:
            if not self._session:
                self.connect()
            self._session.execute(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to update record {record_id} in {table_name}: {e}")
            return False

    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> bool:
        query = f"DELETE FROM {table_name} WHERE {id_column} = %s"
        try:
            if not self._session:
                self.connect()
            self._session.execute(query, [record_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete record {record_id} from {table_name}: {e}")
            return False

    # ── Utility ─────────────────────────────────────────────────────────

    def table_exists(self, table_name: str) -> bool:
        if not self._keyspace:
            return False
        if not self._session:
            self.connect()
        ks_meta = self._cluster.metadata.keyspaces.get(self._keyspace)
        return table_name in ks_meta.tables if ks_meta else False

    def count_records(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        query = f"SELECT COUNT(*) FROM {table_name}"
        params = []
        
        if filters:
            where_clauses = []
            for k, v in filters.items():
                if "__gte" in k:
                    col = k.replace("__gte", "")
                    where_clauses.append(f"{col} >= %s")
                elif "__lte" in k:
                    col = k.replace("__lte", "")
                    where_clauses.append(f"{col} <= %s")
                else:
                    where_clauses.append(f"{k} = %s")
                params.append(v)
            query += " WHERE " + " AND ".join(where_clauses)
            query += " ALLOW FILTERING"

        try:
            if not self._session:
                self.connect()
            row = self._session.execute(query, params).one()
            return row[0] if row else 0
        except Exception as e:
            logger.error(f"Count failed for {table_name}: {e}")
            return 0

    # ── Backward Compatibility Hooks ────────────────────────────────────

    def set_keyspace(self, keyspace: str) -> None:
        """Internal helper to switch keyspaces."""
        if self._session:
            self._session.set_keyspace(keyspace)
            self._keyspace = keyspace

    def get_sales_records(self, **kwargs):
        """Deprecated Use get_record() instead."""
        pass

    def add_sales_record(self, **kwargs):
        """Deprecated Use add_record() instead."""
        pass
