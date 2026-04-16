"""
repo/__init__.py
"""

from typing import Any, Optional, Literal
from repo.base import BaseRepo
from repo.cassandra_repo import CassandraRepository
from repo.postgres_repo import PostgresRepository

def get_repository(repo_type: Literal["cassandra", "postgres", "mongo"] = "cassandra", **kwargs) -> BaseRepo:
    """
    Factory function to retrieve a concrete repository implementation.
    
    Args:
        repo_type: The type of database: 'cassandra' or 'postgres'.
        **kwargs: Arguments passed to the repository constructor.
        
    Returns:
        A concrete repository instance.
    """
    if repo_type == "cassandra":
        return CassandraRepository(**kwargs)
    elif repo_type == "postgres":
        return PostgresRepository(**kwargs)
    elif repo_type == "mongo":
        # Placeholder/Future: Currently MongoDB logic is embedded in some ETL tasks,
        # but a future MongoRepository should be added here.
        raise NotImplementedError("MongoRepository not yet implemented as a BaseRepo.")
    else:
        raise ValueError(f"Unknown repository type: {repo_type}")
