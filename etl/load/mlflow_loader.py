"""
MLflow loader — logs processed datasets and schemas as MLflow artifacts
for experiment tracking and lineage.
"""

from typing import Any, Dict, Optional
from pathlib import Path

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings
from etl.schema.models import DatasetSchema

logger = get_logger(__name__)


@task(
    name="log-to-mlflow",
    retries=2,
    retry_delay_seconds=5,
    description="Log the processed dataset and its schema as MLflow artifacts.",
)
def log_to_mlflow(
    data_path: str,
    schema: DatasetSchema,
    run_name: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Create an MLflow run and log the dataset file + schema JSON
    as artifacts, along with key metrics.

    Args:
        data_path:     Path to the processed data file (Parquet/CSV).
        schema:        The DatasetSchema from the identification step.
        run_name:      Optional MLflow run name.
        extra_params:  Additional parameters to log.

    Returns:
        The MLflow run ID, or None if MLflow is disabled or unavailable.
    """
    settings = get_settings().load

    if not settings.mlflow_tracking:
        logger.info("MLflow tracking is disabled — skipping.")
        return None

    try:
        import mlflow
    except ImportError:
        logger.warning("mlflow is not installed — skipping MLflow logging.")
        return None

    run_name = run_name or f"etl-{schema.source_name}"

    try:
        mlflow.set_experiment(settings.mlflow_experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            # ── Log parameters ──────────────────────────────────
            mlflow.log_param("source_name", schema.source_name)
            mlflow.log_param("source_type", schema.source_type)
            mlflow.log_param("field_count", schema.field_count)
            mlflow.log_param("schema_version", schema.version)

            if extra_params:
                for k, v in extra_params.items():
                    mlflow.log_param(k, v)

            # ── Log metrics ─────────────────────────────────────
            mlflow.log_metric("record_count", schema.record_count)
            mlflow.log_metric("issue_count", len(schema.issues))
            mlflow.log_metric(
                "nullable_field_count",
                len(schema.nullable_fields()),
            )
            mlflow.log_metric(
                "nested_field_count",
                len(schema.nested_fields()),
            )

            # ── Log schema JSON as artifact ─────────────────────
            schema_json = schema.model_dump_json(indent=2)
            schema_path = Path(data_path).parent / "schema.json"
            schema_path.write_text(schema_json, encoding="utf-8")
            mlflow.log_artifact(str(schema_path), artifact_path="schema")

            # ── Log data file as artifact ───────────────────────
            data_file = Path(data_path)
            if data_file.exists() and data_file.is_file():
                mlflow.log_artifact(str(data_file), artifact_path="datasets")

            run_id = run.info.run_id
            logger.info(
                f"Logged to MLflow: experiment='{settings.mlflow_experiment_name}', "
                f"run_id={run_id}"
            )
            return run_id

    except Exception as exc:
        logger.error(f"MLflow logging failed: {exc}")
        return None
