"""
Pipeline configuration and settings.
Centralises all tuneable parameters for the ETL pipeline.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from pathlib import Path
import os


class CassandraSettings(BaseModel):
    """Cassandra / ScyllaDB connection settings."""
    contact_points: List[str] = Field(default_factory=lambda: ["127.0.0.1"])
    port: int = 9042
    username: Optional[str] = os.getenv("CASSANDRA_USERNAME")
    password: Optional[str] = os.getenv("CASSANDRA_PASSWORD")
    keyspace: Optional[str] = os.getenv("CASSANDRA_KEYSPACE")
    default_table: str = "Sales"


class KafkaSettings(BaseModel):
    """Kafka consumer settings."""
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id: str = "moshtari-etl"
    auto_offset_reset: str = "earliest"
    max_messages: int = 1000
    poll_timeout_ms: int = 5000


class ExtractSettings(BaseModel):
    """Settings for the extract phase."""
    cassandra: CassandraSettings = Field(default_factory=CassandraSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    api_timeout_seconds: int = 30
    api_max_retries: int = 3


class SchemaSettings(BaseModel):
    """Settings for schema identification."""
    sample_size_for_inference: int = 1000
    nested_detection_sample: int = 100
    null_threshold_warning: float = 0.5
    null_threshold_critical: float = 0.9
    schema_history_dir: Path = Path("data/schemas")
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
    output_dir: Path = Path("data/processed")
    output_format: Literal["parquet", "csv"] = "parquet"
    mlflow_tracking: bool = True
    mlflow_experiment_name: str = "moshtari-etl"
    load_retries: int = 3
    retry_delay_seconds: int = 5


class PipelineSettings(BaseModel):
    """Root configuration aggregating all pipeline settings."""
    extract: ExtractSettings = Field(default_factory=ExtractSettings)
    schema: SchemaSettings = Field(default_factory=SchemaSettings)
    transform: TransformSettings = Field(default_factory=TransformSettings)
    load: LoadSettings = Field(default_factory=LoadSettings)
    log_level: str = "INFO"


_settings: Optional[PipelineSettings] = None


def get_settings() -> PipelineSettings:
    """Return the singleton pipeline settings instance."""
    global _settings
    if _settings is None:
        _settings = PipelineSettings()
    return _settings
