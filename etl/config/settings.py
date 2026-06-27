"""
Minimal settings stub for standalone/local builds.
Replaces the full ETL settings module so that service imports resolve without
requiring the entire ETL pipeline package.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CassandraSettings:
    """Stub Cassandra settings — returns env vars or safe defaults."""
    contact_points: List[str] = field(
        default_factory=lambda: os.getenv("CASSANDRA_CONTACT_POINTS", "127.0.0.1").split(",")
    )
    port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    username: str = os.getenv("CASSANDRA_USERNAME", "")
    password: str = os.getenv("CASSANDRA_PASSWORD", "")
    keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "moshtari")
    default_table: str = os.getenv("CASSANDRA_TABLE", "sales")


@dataclass
class PostgresSettings:
    """Postgres connection settings from environment or defaults."""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    dbname: str = os.getenv("POSTGRES_DB", "moshtari")
    uri: Optional[str] = os.getenv("DATABASE_URL", None)


@dataclass
class MongoSettings:
    uri: str = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    database: str = os.getenv("MONGO_DB", "mushtari")


@dataclass
class ExtractSettings:
    cassandra: CassandraSettings = field(default_factory=CassandraSettings)
    postgres: PostgresSettings = field(default_factory=PostgresSettings)
    mongo: MongoSettings = field(default_factory=MongoSettings)


@dataclass
class Settings:
    extract: ExtractSettings = field(default_factory=ExtractSettings)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the singleton settings object."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
