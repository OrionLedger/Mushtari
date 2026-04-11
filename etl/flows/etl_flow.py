"""
Main ETL Pipeline Flow
======================

Orchestrates the full Extract → Schema → Transform → Load pipeline
using Prefect @flow and @task decorators.

Supports multiple data sources (database, CSV/Excel, Kafka, API)
through a unified ``source_type`` parameter.
"""

from typing import Any, Dict, List, Literal, Optional
from pathlib import Path

import pandas as pd
from prefect import flow, task
from prefect.logging import get_run_logger

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings

# ── Extract tasks ────────────────────────────────────────────────────
from etl.extract.database import extract_from_database
from etl.gatekeeper.validator import apply_gatekeeper_rules
from etl.extract.file import extract_from_csv, extract_from_excel
from etl.extract.kafka import extract_from_kafka
from etl.extract.api import extract_from_api

# ── Schema tasks ─────────────────────────────────────────────────────
from etl.schema.identifier import identify_schema
from etl.schema.validator import (
    validate_schema,
    detect_schema_drift,
    load_latest_schema,
)

# ── Transform tasks ──────────────────────────────────────────────────
from etl.transform.cleaner import clean
from etl.transform.normalizer import normalize
from etl.transform.caster import cast_types
from etl.transform.validator import validate_data

# ── Load tasks ───────────────────────────────────────────────────────
from etl.load.file import load_to_parquet, load_to_csv
from etl.load.database import load_to_database
from etl.load.mlflow_loader import log_to_mlflow

logger = get_logger(__name__)


# ── Unified extract dispatcher ──────────────────────────────────────

@task(name="dispatch-extract")
def dispatch_extract(
    source_type: str,
    source_config: Dict[str, Any],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Route extraction to the appropriate extractor based on ``source_type``.

    Args:
        source_type:    One of "database", "csv", "excel", "kafka", "api".
        source_config:  Keyword arguments forwarded to the chosen extractor.

    Returns:
        (DataFrame, metadata_dict)
    """
    extractors = {
        "database": extract_from_database,
        "csv":      extract_from_csv,
        "excel":    extract_from_excel,
        "kafka":    extract_from_kafka,
        "api":      extract_from_api,
    }

    if source_type not in extractors:
        raise ValueError(
            f"Unknown source_type '{source_type}'. "
            f"Supported: {list(extractors.keys())}"
        )

    extractor_fn = extractors[source_type]
    return extractor_fn.fn(**source_config)


# ── Main ETL Flow ───────────────────────────────────────────────────

@flow(
    name="moshtari-etl-pipeline",
    description="Full Extract → Schema → Transform → Load pipeline for "
                "the Moshtari demand forecasting platform.",
    log_prints=True,
)
def etl_pipeline_flow(
    # ── Source configuration ─────────────────────────────────────
    source_type: Literal["database", "csv", "excel", "kafka", "api"] = "database",
    source_config: Optional[Dict[str, Any]] = None,
    # ── Transform configuration ─────────────────────────────────
    outliers_strategy: str = "drop",
    missing_data_strategy: str = "impute",
    normalize_strategy: str = "none",
    # ── Load configuration ──────────────────────────────────────
    output_filename: Optional[str] = None,
    output_format: str = "parquet",
    load_to_db: bool = False,
    db_type: str = "cassandra",
    db_uri: Optional[str] = None,
    db_table_name: str = "processed_sales",
    track_in_mlflow: bool = True,
    # ── Pipeline options ────────────────────────────────────────
    strict_gatekeeper: bool = False,
    check_schema_drift: bool = True,
    fail_on_validation_error: bool = True,
) -> Dict[str, Any]:
    """
    Execute the full Moshtari ETL pipeline.

    This flow:
        1. **Extracts** data from the specified source.
        2. **Identifies** the schema automatically (types, nulls, nesting).
        3. **Detects** schema drift against the previous run (optional).
        4. **Transforms** the data: cleans, casts types, normalises, validates.
        5. **Loads** the processed data to file (Parquet/CSV), optionally
           to the database and MLflow.

    Args:
        source_type:             Data source type.
        source_config:           Keyword arguments for the chosen extractor.
        outliers_strategy:       Outlier handling strategy.
        missing_data_strategy:   Missing value handling strategy.
        normalize_strategy:      Normalisation strategy.
        output_filename:         Output file name (auto-generated if None).
        output_format:           "parquet" or "csv".
        load_to_db:              Also write results to target database.
        db_type:                 Type of the target db (cassandra, mongo, postgres).
        db_uri:                  Connection URI for the target DB.
        db_table_name:           Target table for database load.
        track_in_mlflow:         Log results to MLflow.
        strict_gatekeeper:       Halt flow strongly if business rules fail.
        check_schema_drift:      Compare schema to previous run.
        fail_on_validation_error: Raise on data validation failure.

    Returns:
        Summary dict with pipeline results.
    """
    source_config = source_config or {}
    settings = get_settings()
    results: Dict[str, Any] = {
        "source_type": source_type,
        "status": "started",
    }

    print(f"{'='*60}")
    print(f"  Moshtari ETL Pipeline")
    print(f"  Source: {source_type}")
    print(f"{'='*60}")

    # ================================================================
    # STEP 1: EXTRACT
    # ================================================================
    print("\n▶ Step 1/5: EXTRACT")

    df, extract_metadata = dispatch_extract(
        source_type=source_type,
        source_config=source_config,
    )

    results["extract"] = extract_metadata
    source_name = extract_metadata.get("source_name", "unknown")
    print(f"  ✓ Extracted {len(df)} rows from {source_name}")

    if df.empty:
        results["status"] = "failed"
        results["error"] = "No data extracted — pipeline aborted."
        print("  ✗ No data extracted. Aborting pipeline.")
        return results
        
    # ================================================================
    # STEP 1.5: GATEKEEPER VALIDATION
    # ================================================================
    print("\n▶ Step 1.5/5: GATEKEEPER VALIDATION")
    
    try:
        df = apply_gatekeeper_rules(df, strict_halt=strict_gatekeeper)
        print(f"  ✓ Gatekeeper passed. Rows remaining: {len(df)}")
    except Exception as e:
        results["status"] = "failed"
        results["error"] = f"Gatekeeper validation aborted: {e}"
        print(f"  ✗ {results['error']}")
        return results

    if df.empty:
        results["status"] = "failed"
        results["error"] = "All data dropped by Gatekeeper — pipeline aborted."
        print("  ✗ All data dropped by Gatekeeper. Aborting pipeline.")
        return results

    # ================================================================
    # STEP 2: IDENTIFY SCHEMA
    # ================================================================
    print("\n▶ Step 2/5: IDENTIFY SCHEMA")

    schema = identify_schema(
        df=df,
        source_name=source_name,
        source_type=source_type,
    )

    results["schema"] = {
        "field_count": schema.field_count,
        "record_count": schema.record_count,
        "issues": len(schema.issues),
        "has_critical": schema.has_critical_issues(),
        "nullable_fields": schema.nullable_fields(),
        "nested_fields": schema.nested_fields(),
    }

    print(f"  ✓ {schema.summary()}")

    # Field details
    for name, field in schema.fields.items():
        nested_tag = " [NESTED]" if field.is_nested else ""
        null_tag = f" ({field.null_percentage:.0%} null)" if field.nullable else ""
        print(
            f"    • {name}: {field.inferred_type.value}"
            f"{null_tag}{nested_tag}"
        )

    # Log issues
    if schema.issues:
        print(f"  ⚠ {len(schema.issues)} issue(s) detected:")
        for issue in schema.issues:
            icon = "✗" if issue.severity.value == "critical" else "⚠"
            print(f"    {icon} [{issue.severity.value}] {issue.field}: {issue.message}")

    # ── Schema drift detection ──────────────────────────────────
    if check_schema_drift:
        previous_schema = load_latest_schema(
            source_name=source_name,
            schema_dir=settings.schema.schema_history_dir,
        )
        if previous_schema is not None:
            drift_report = detect_schema_drift(
                previous=previous_schema,
                current=schema,
            )
            results["schema_drift"] = {
                "has_breaking_changes": drift_report.has_breaking_changes,
                "added_fields": drift_report.added_fields,
                "removed_fields": drift_report.removed_fields,
                "type_changes": drift_report.type_changes,
            }
            if drift_report.has_breaking_changes:
                print("  ⚠ BREAKING schema drift detected!")
                for detail in drift_report.details:
                    print(f"    → {detail}")
            elif drift_report.details:
                print(f"  ℹ Non-breaking changes: {len(drift_report.details)}")
        else:
            print("  ℹ No previous schema found — first run for this source.")

    # ================================================================
    # STEP 3: TRANSFORM
    # ================================================================
    print("\n▶ Step 3/5: TRANSFORM")

    # 3a. Cast types based on schema
    print("  → Casting types...")
    df = cast_types(df=df, schema=schema, errors="coerce")

    # 3b. Clean (handle missing values and outliers)
    #     Only apply to numeric-heavy DataFrames
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        print(f"  → Cleaning ({len(numeric_cols)} numeric columns)...")
        df_numeric = df[numeric_cols].copy()
        df_numeric = clean(
            df=df_numeric,
            outliers_strategy=outliers_strategy,
            missing_data=missing_data_strategy,
        )
        # Rejoin with non-numeric columns
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
        if non_numeric_cols:
            df = pd.concat(
                [df_numeric, df[non_numeric_cols].loc[df_numeric.index]],
                axis=1,
            )
        else:
            df = df_numeric
    else:
        print("  → No numeric columns to clean — skipping.")

    # 3c. Normalise
    if normalize_strategy != "none" and len(numeric_cols) > 0:
        print(f"  → Normalising (strategy={normalize_strategy})...")
        df_numeric = df.select_dtypes(include=["number"])
        df_numeric = normalize(df=df_numeric, strategy=normalize_strategy)
        df[df_numeric.columns] = df_numeric
    else:
        print("  → Normalisation skipped.")

    # 3d. Validate transformed data
    print("  → Validating...")
    df = validate_data(
        df=df,
        schema=schema,
        fail_on_error=fail_on_validation_error,
    )

    results["transform"] = {
        "rows_after": len(df),
        "columns_after": len(df.columns),
    }
    print(f"  ✓ Transform complete: {len(df)} rows × {len(df.columns)} columns")

    # ================================================================
    # STEP 4: LOAD
    # ================================================================
    print("\n▶ Step 4/5: LOAD")

    # 4a. File output
    if output_format == "parquet":
        data_path = load_to_parquet(df=df, filename=output_filename)
    else:
        data_path = load_to_csv(df=df, filename=output_filename)

    results["load"] = {"file_path": data_path}
    print(f"  ✓ Saved to {data_path}")

    # 4b. Database output (optional)
    if load_to_db:
        print(f"  → Loading to target database '{db_type}' in table '{db_table_name}'...")
        db_summary = load_to_database(
            df=df, 
            table_name=db_table_name,
            db_type=db_type,
            connection_uri=db_uri
        )
        results["load"]["database"] = db_summary
        print(
            f"  ✓ Database: {db_summary['inserted']}/{db_summary['total']} "
            f"inserted"
        )

    # 4c. MLflow tracking (optional)
    if track_in_mlflow:
        print("  → Logging to MLflow...")
        run_id = log_to_mlflow(
            data_path=data_path,
            schema=schema,
            extra_params={
                "source_type": source_type,
                "outliers_strategy": outliers_strategy,
                "missing_data_strategy": missing_data_strategy,
                "normalize_strategy": normalize_strategy,
            },
        )
        results["load"]["mlflow_run_id"] = run_id
        if run_id:
            print(f"  ✓ MLflow run: {run_id}")

    # ================================================================
    # STEP 5: SUMMARY
    # ================================================================
    print(f"\n{'='*60}")
    print(f"  ✓ Pipeline completed successfully")
    print(f"    Rows:    {extract_metadata['record_count']} → {len(df)}")
    print(f"    Schema:  {schema.field_count} fields, {len(schema.issues)} issues")
    print(f"    Output:  {data_path}")
    print(f"{'='*60}\n")

    results["status"] = "completed"
    return results


# ── Convenience sub-flows ───────────────────────────────────────────

@flow(
    name="etl-from-csv",
    description="Shortcut: run the full ETL pipeline on a CSV file.",
    log_prints=True,
)
def etl_from_csv_flow(
    file_path: str,
    output_filename: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run the ETL pipeline with a CSV source."""
    return etl_pipeline_flow(
        source_type="csv",
        source_config={"file_path": file_path},
        output_filename=output_filename,
        **kwargs,
    )


@flow(
    name="etl-from-database",
    description="Shortcut: run the full ETL pipeline from Cassandra.",
    log_prints=True,
)
def etl_from_database_flow(
    table_name: str = "Sales",
    product_id: Optional[int] = None,
    columns: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_filename: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run the ETL pipeline from the Cassandra database."""
    return etl_pipeline_flow(
        source_type="database",
        source_config={
            "table_name": table_name,
            "product_id": product_id,
            "columns": columns,
            "start_date": start_date,
            "end_date": end_date,
        },
        output_filename=output_filename or f"product_{product_id}",
        **kwargs,
    )


@flow(
    name="etl-from-kafka",
    description="Shortcut: run the full ETL pipeline from a Kafka topic.",
    log_prints=True,
)
def etl_from_kafka_flow(
    topic: str,
    max_messages: int = 1000,
    output_filename: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run the ETL pipeline from a Kafka topic."""
    return etl_pipeline_flow(
        source_type="kafka",
        source_config={
            "topic": topic,
            "max_messages": max_messages,
        },
        output_filename=output_filename or f"kafka_{topic}",
        **kwargs,
    )


@flow(
    name="etl-from-api",
    description="Shortcut: run the full ETL pipeline from an external API.",
    log_prints=True,
)
def etl_from_api_flow(
    base_url: str,
    endpoint: str = "",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_path: Optional[str] = None,
    output_filename: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run the ETL pipeline from an external REST API."""
    return etl_pipeline_flow(
        source_type="api",
        source_config={
            "base_url": base_url,
            "endpoint": endpoint,
            "params": params,
            "headers": headers,
            "json_path": json_path,
        },
        output_filename=output_filename,
        **kwargs,
    )
