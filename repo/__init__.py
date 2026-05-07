"""
repo/__init__.py
"""

from typing import Any, Optional, Literal
from repo.base import BaseRepo
from repo.cassandra_repo import CassandraRepository
from repo.postgres_repo import PostgresRepository

class DatabaseRegistry:
    """
    Singleton manager for persistent database repositories.
    Ensures that connections are reused across the application lifecycle.
    """
    _instances = {}

    @classmethod
    def get_shared(cls, repo_type: str, **kwargs) -> BaseRepo:
        # Create a hashable cache key from type and connection parameters.
        # Lists (like contact_points) are not hashable, so we convert them to tuples.
        hashable_args = []
        for k, v in sorted(kwargs.items()):
            if isinstance(v, list):
                hashable_args.append((k, tuple(v)))
            else:
                hashable_args.append((k, v))
        
        key = (repo_type, tuple(hashable_args))
        
        if key not in cls._instances:
            if repo_type == "cassandra":
                cls._instances[key] = CassandraRepository(**kwargs)
            elif repo_type == "postgres":
                cls._instances[key] = PostgresRepository(**kwargs)
            else:
                raise ValueError(f"Unknown repository type: {repo_type}")
                
        # Optional: Auto-connect if dropped
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
            except:
                pass
        cls._instances.clear()

def get_repository(
    repo_type: Literal["cassandra", "postgres", "mongo"] = "cassandra", 
    shared: bool = True,
    **kwargs
) -> BaseRepo:
    """
    Factory function to retrieve a repository implementation.
    
    Args:
        repo_type: The type of database: 'cassandra' or 'postgres'.
        shared: If True, returns a persistent instance from the Registry.
        **kwargs: Arguments passed to the repository constructor.
    """
    if repo_type == "mongo":
        raise NotImplementedError("MongoRepository not yet implemented as a BaseRepo.")
        
    if shared:
        return DatabaseRegistry.get_shared(repo_type, **kwargs)
        
    # Non-shared (fresh connection)
    if repo_type == "cassandra":
        return CassandraRepository(**kwargs)
    elif repo_type == "postgres":
        return PostgresRepository(**kwargs)
    
    raise ValueError(f"Unknown repository type: {repo_type}")
