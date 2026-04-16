"""
Pipeline configuration and settings.
Centralises all tuneable parameters for the ETL pipeline.
Loads environment variables from .env files.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CassandraSettings(BaseModel):
    """Cassandra / ScyllaDB connection settings."""
    contact_points: List[str] = Field(
        default_factory=lambda: os.getenv("CASSANDRA_CONTACT_POINTS", "127.0.0.1").split(",")
    )
    port: int = int(os.getenv("CASSANDRA_PORT", 9042))
    username: Optional[str] = os.getenv("CASSANDRA_USERNAME")
    password: Optional[str] = os.getenv("CASSANDRA_PASSWORD")
    keyspace: Optional[str] = os.getenv("CASSANDRA_KEYSPACE")
    default_table: str = os.getenv("CASSANDRA_DEFAULT_TABLE", "sales")


class KafkaSettings(BaseModel):
    """Kafka consumer settings."""
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id: str = os.getenv("KAFKA_GROUP_ID", "moshtari-etl")
    auto_offset_reset: str = "earliest"
    max_messages: int = 1000
    poll_timeout_ms: int = 5000


class PostgresSettings(BaseModel):
    """PostgreSQL connection settings."""
    uri: Optional[str] = os.getenv("POSTGRES_URI")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", 5432))
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    dbname: str = os.getenv("POSTGRES_DB", "postgres")


class MongoSettings(BaseModel):
    """MongoDB connection settings."""
    uri: str = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    database: str = os.getenv("MONGO_DB", "mushtari")


class ExtractSettings(BaseModel):
    """Settings for the extract phase."""
    cassandra: CassandraSettings = Field(default_factory=CassandraSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    mongo: MongoSettings = Field(default_factory=MongoSettings)
    api_timeout_seconds: int = 30
    api_max_retries: int = 3


class SchemaSettings(BaseModel):
    """Settings for schema identification."""
    sample_size_for_inference: int = 1000
    nested_detection_sample: int = 100
    null_threshold_warning: float = 0.5
    null_threshold_critical: float = 0.9
    schema_history_dir: Path = Path(os.getenv("SCHEMA_HISTORY_DIR", "data/schemas"))
    detect_drift: bool = True


class TransformSettings(BaseModel):
    """Settings for the transform phase."""
    outliers_strategy: Literal["drop", "stl_dec", "rolling", "hampel"] = "drop"
    missing_data_strategy: Literal["drop", "impute", "none"] = "impute"
    normalize_strategy: Literal["standard", "minmax", "robust", "none"] = "none"
    min_rows_required: int = 10
    max_null_ratio: float = 0.3


class LoadSettings(BaseModel):
    """Settings for the load phase."""
    output_dir: Path = Path(os.getenv("PROCESSED_DATA_DIR", "data/processed"))
    output_format: Literal["parquet", "csv"] = os.getenv("OUTPUT_FORMAT", "parquet")
    mlflow_tracking: bool = os.getenv("MLFLOW_TRACKING", "True").lower() == "true"
    mlflow_experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "moshtari-etl")
    load_retries: int = 3
    retry_delay_seconds: int = 5


class PipelineSettings(BaseModel):
    """Root configuration aggregating all pipeline settings."""
    extract: ExtractSettings = Field(default_factory=ExtractSettings)
    schema: SchemaSettings = Field(default_factory=SchemaSettings)
    transform: TransformSettings = Field(default_factory=TransformSettings)
    load: LoadSettings = Field(default_factory=LoadSettings)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    models_dir: Path = Path(os.getenv("MODELS_DIR", "./models"))


_settings: Optional[PipelineSettings] = None


def get_settings() -> PipelineSettings:
    """Return the singleton pipeline settings instance."""
    global _settings
    if _settings is None:
        _settings = PipelineSettings()
    return _settings
