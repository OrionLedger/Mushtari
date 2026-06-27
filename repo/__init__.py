"""
repo/__init__.py

Repository factory that supports PostgreSQL, SQLite, and Cassandra backends.
When DATABASE_TYPE=sqlite (or the environment variable is set), all consumers
calling get_repository("postgres", ...) are automatically routed to SQLite,
enabling zero-code-change local deployment.
"""

import os
from typing import Any, Optional, Literal
from repo.base import BaseRepo
from repo.sqlite_repo import SQLiteRepository
from repo.postgres_repo import PostgresRepository


class DatabaseRegistry:
    """
    Singleton manager for persistent database repositories.
    Ensures that connections are reused across the application lifecycle.
    """
    _instances = {}

    @classmethod
    def get_shared(cls, repo_type: str, **kwargs) -> BaseRepo:
        # Resolve aliases
        resolved = _resolve_type(repo_type)

        # Create a hashable cache key from type and connection parameters.
        hashable_args = []
        for k, v in sorted(kwargs.items()):
            if isinstance(v, list):
                hashable_args.append((k, tuple(v)))
            else:
                hashable_args.append((k, v))

        key = (resolved, tuple(hashable_args))

        if key not in cls._instances:
            if resolved == "sqlite":
                db_path = kwargs.get("db_path") or os.getenv("DATABASE_URL", "./data/moshtari.db")
                # Strip sqlite:/// prefix if present
                if db_path.startswith("sqlite:///"):
                    db_path = db_path[len("sqlite:///"):]
                cls._instances[key] = SQLiteRepository(db_path=db_path)
            elif resolved == "postgres":
                cls._instances[key] = PostgresRepository(**kwargs)
            else:
                raise ValueError(f"Unknown repository type: {resolved} (from {repo_type})")

        # Auto-connect if dropped
        repo = cls._instances[key]
        if not repo.is_connected():
            repo.connect()

        return repo

    @classmethod
    def dispose(cls):
        """Cleanly shutdown all shared connections."""
        for repo in cls._instances.values():
            try:
                repo.close()
            except Exception:
                pass
        cls._instances.clear()


def _resolve_type(repo_type: str) -> str:
    """
    Resolve the repository type, applying the SQLite routing override.

    When DATABASE_TYPE=sqlite is set, any request for 'postgres' or 'cassandra'
    is transparently routed to 'sqlite'. If DATABASE_TYPE is not set, falls
    back to checking DATABASE_URL for sqlite:/// prefix.
    This allows all existing service code to work unchanged when deployed locally.
    """
    # Check environment override
    db_type_env = os.getenv("DATABASE_TYPE", "").lower().strip()
    db_url_env = os.getenv("DATABASE_URL", "").lower().strip()

    if repo_type == "sqlite":
        return "sqlite"

    if repo_type in ("postgres", "cassandra"):
        # Route to SQLite if DATABASE_TYPE explicitly says so
        if db_type_env == "sqlite":
            return "sqlite"
        # If DATABASE_TYPE is not set, check DATABASE_URL as fallback
        if not db_type_env and db_url_env.startswith("sqlite:///"):
            return "sqlite"
        return repo_type

    # passthrough for any other type
    return repo_type


def get_repository(
    repo_type: Literal["cassandra", "postgres", "sqlite"] = "postgres",
    shared: bool = True,
    **kwargs
) -> BaseRepo:
    """
    Factory function to retrieve a repository implementation.

    Automatically routes 'postgres' requests to SQLite when
    DATABASE_TYPE=sqlite is set — enabling zero-code-change local deployment.

    Args:
        repo_type: 'postgres', 'sqlite', or 'cassandra'.
        shared: If True, returns a persistent instance from the Registry.
        **kwargs: Arguments passed to the repository constructor.

    Returns:
        A concrete BaseRepo instance.
    """
    resolved = _resolve_type(repo_type)

    if shared:
        return DatabaseRegistry.get_shared(resolved, **kwargs)

    # Non-shared (fresh connection)
    if resolved == "sqlite":
        db_path = kwargs.get("db_path") or os.getenv("DATABASE_URL", "./data/moshtari.db")
        if db_path.startswith("sqlite:///"):
            db_path = db_path[len("sqlite:///"):]
        return SQLiteRepository(db_path=db_path)
    elif resolved == "postgres":
        return PostgresRepository(**kwargs)

    raise ValueError(f"Unknown repository type: {resolved} (from {repo_type})")
