"""
repo/base.py

Abstract base class for all data repository implementations in Moshtari.
Defines the contract that any concrete repository must fulfill, completely
independent of any specific database technology.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepo(ABC):
    """
    Abstract base repository defining the standard interface for all
    data access layers in the Moshtari platform.

    Any concrete repository (Cassandra, PostgreSQL, MongoDB, etc.) must
    implement every abstract method defined here. This ensures the ETL
    pipeline and service layers remain decoupled from the underlying
    storage engine.
    """

    # ── Connection Lifecycle ────────────────────────────────────────────

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Establish a connection to the underlying data store.

        Args:
            **kwargs: Connection parameters specific to the implementation
                      (e.g., host, port, credentials, keyspace).
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Gracefully close and release the connection to the data store.
        Should be safe to call even if connect() was never called.
        """
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check whether the repository currently holds an active connection.

        Returns:
            True if connected and ready, False otherwise.
        """
        ...

    # ── Read Operations ─────────────────────────────────────────────────

    @abstractmethod
    def get_record(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve records from the data store.

        Args:
            table_name: The target table / collection / keyspace to query.
            filters:    Optional dict of column → value equality constraints
                        used to narrow the result set.
            columns:    List of column names to project. Fetches all if None.

        Returns:
            A list of dicts where each dict represents a single row/document.
        """
        ...

    @abstractmethod
    def get_record_by_id(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single record by its primary identifier.

        Args:
            table_name:  The target table / collection to query.
            record_id:   The value of the primary key to look up.
            id_column:   The name of the primary key column (default: 'id').

        Returns:
            A dict representing the record, or None if not found.
        """
        ...

    # ── Write Operations ────────────────────────────────────────────────

    @abstractmethod
    def add_record(
        self,
        table_name: str,
        record: Dict[str, Any],
    ) -> bool:
        """
        Insert a single record into the data store.

        Args:
            table_name: The target table / collection to write to.
            record:     A dict mapping column names to their values.

        Returns:
            True if the record was inserted successfully, False otherwise.
        """
        ...

    @abstractmethod
    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, int]:
        """
        Insert multiple records in an efficient batch operation.

        Args:
            table_name:  The target table / collection.
            records:     A list of record dicts to insert.
            batch_size:  Number of records to commit per batch (for chunking).

        Returns:
            A summary dict: {"total": int, "inserted": int, "failed": int}.
        """
        ...

    @abstractmethod
    def update_record(
        self,
        table_name: str,
        record_id: Any,
        updates: Dict[str, Any],
        id_column: str = "id",
    ) -> bool:
        """
        Update fields on an existing record.

        Args:
            table_name:  The target table / collection.
            record_id:   The primary key value identifying the record.
            updates:     A dict of column → new_value pairs to apply.
            id_column:   The name of the primary key column (default: 'id').

        Returns:
            True if the update was applied, False if the record was not found.
        """
        ...

    @abstractmethod
    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
    ) -> bool:
        """
        Remove a single record from the data store by its primary key.

        Args:
            table_name:  The target table / collection.
            record_id:   The primary key value of the record to delete.
            id_column:   The name of the primary key column (default: 'id').

        Returns:
            True if the record was deleted, False if not found.
        """
        ...

    # ── Utility ─────────────────────────────────────────────────────────

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        Check whether a given table / collection exists in the data store.

        Args:
            table_name: Name of the table or collection to verify.

        Returns:
            True if the table exists, False otherwise.
        """
        ...

    @abstractmethod
    def count_records(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count records in a table, optionally applying equality filters.

        Args:
            table_name: The target table / collection.
            filters:    Optional dict of column → value equality constraints.

        Returns:
            The total number of matching records.
        """
        ...

    # ── Context Manager Support ──────────────────────────────────────────

    def __enter__(self) -> "BaseRepo":
        """Allow use as a context manager: `with MyRepo() as repo:`."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Automatically close the connection on context manager exit."""
        self.close()

    # ── Dunder ──────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        status = "connected" if self.is_connected() else "disconnected"
        return f"<{self.__class__.__name__} [{status}]>"
