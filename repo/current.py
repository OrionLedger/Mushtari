"""
repo/current.py

SINGLE injection point for the active database repository.

ALL service code should call get_active_repository() instead of
get_repository("cassandra", ...) or get_repository("postgres", ...) directly.

To switch the database backend, change DATABASE_TYPE in .env:
    DATABASE_TYPE=postgres   → PostgreSQL
    DATABASE_TYPE=sqlite     → SQLite (local)

No other code changes needed — this is the one and only place
that decides which backend is active.
"""

import os
from repo import get_repository

_active_repo = None


def get_active_repository():
    """
    Return the single active repository for the application.

    The backend type is determined by the DATABASE_TYPE env var:
      - "postgres" → PostgresRepository
      - "sqlite"   → SQLiteRepository (automatically routed via _resolve_type)
      - unset      → defaults to postgres

    The instance is cached as a module-level singleton so all callers
    share the same connection pool.
    """
    global _active_repo
    if _active_repo is None:
        db_type = os.getenv("DATABASE_TYPE", "postgres")
        _active_repo = get_repository(db_type, shared=True)
    return _active_repo


def reset_active_repository():
    """Force re-creation on next call (useful after .env changes at runtime)."""
    global _active_repo
    _active_repo = None
