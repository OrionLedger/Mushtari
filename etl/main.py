"""
Moshtari ETL — Main Entry Point
================================

Run this file directly to execute the ETL pipeline:

    python -m etl.main

Or import and call from anywhere:

    from etl.main import run_etl
    run_etl(source_type="csv", source_config={"file_path": "data/raw/sales.csv"})
"""

import sys
import argparse
from typing import Optional

from etl.flows.etl_flow import (
    etl_pipeline_flow,
    etl_from_csv_flow,
    etl_from_database_flow,
    etl_from_kafka_flow,
    etl_from_api_flow,
)


def run_etl(
    source_type: str = "database",
    source_config: Optional[dict] = None,
    **kwargs,
) -> dict:
    """
    Programmatic entry point for the ETL pipeline.

    Args:
        source_type:    "database", "csv", "excel", "kafka", or "api".
        source_config:  Keyword arguments for the chosen extractor.
        **kwargs:       Additional pipeline configuration.

    Returns:
        Pipeline results dictionary.
    """
    return etl_pipeline_flow(
        source_type=source_type,
        source_config=source_config or {},
        **kwargs,
    )


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Moshtari ETL Pipeline — Extract, Schema, Transform, Load",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # ETL from a CSV file
  python -m etl.main --source csv --file data/raw/sales.csv

  # ETL from the database for a specific product
  python -m etl.main --source database --product-id 1

  # ETL from a Kafka topic
  python -m etl.main --source kafka --topic sales-events

  # ETL from an external API
  python -m etl.main --source api --url https://api.example.com/sales
        """,
    )

    # Source selection
    parser.add_argument(
        "--source", "-s",
        choices=["database", "csv", "excel", "kafka", "api"],
        default="database",
        help="Data source type (default: database)",
    )

    # File sources
    parser.add_argument("--file", "-f", help="Path to CSV or Excel file")

    # Database sources
    parser.add_argument("--product-id", "-p", type=int, help="Product ID to extract")
    parser.add_argument("--table", default="Sales", help="Database table name")
    parser.add_argument("--start-date", help="Start date filter (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date filter (YYYY-MM-DD)")

    # Kafka sources
    parser.add_argument("--topic", "-t", help="Kafka topic name")
    parser.add_argument("--max-messages", type=int, default=1000, help="Max Kafka messages")

    # API sources
    parser.add_argument("--url", "-u", help="API base URL")
    parser.add_argument("--endpoint", default="", help="API endpoint path")
    parser.add_argument("--json-path", help="JSON path to data array (e.g. data.results)")

    # Transform options
    parser.add_argument(
        "--outliers", default="drop",
        choices=["drop", "stl_dec", "rolling", "hampel"],
        help="Outlier handling strategy",
    )
    parser.add_argument(
        "--missing", default="impute",
        choices=["drop", "impute", "none"],
        help="Missing data strategy",
    )
    parser.add_argument(
        "--normalize", default="none",
        choices=["standard", "minmax", "robust", "none"],
        help="Normalisation strategy",
    )

    # Load options
    parser.add_argument("--output", "-o", help="Output filename (without extension)")
    parser.add_argument(
        "--format", default="parquet",
        choices=["parquet", "csv"],
        help="Output file format",
    )
    parser.add_argument(
        "--load-to-db", action="store_true",
        help="Also load results into the target database",
    )
    parser.add_argument(
        "--db-type", default="cassandra",
        choices=["cassandra", "mongo", "postgres"],
        help="Target database to load into (default: cassandra)",
    )
    parser.add_argument(
        "--db-uri", default=None,
        help="Connection string/URI for target databases (like Postgres or Mongo)",
    )
    parser.add_argument(
        "--no-mlflow", action="store_true",
        help="Disable MLflow tracking",
    )
    parser.add_argument(
        "--no-drift-check", action="store_true",
        help="Skip schema drift detection",
    )
    parser.add_argument(
        "--strict-gatekeeper", action="store_true",
        help="Halt pipeline completely if Gatekeeper detects business rule violations (instead of heavily dropping invalid rows)",
    )

    args = parser.parse_args()

    # ── Build source_config based on source type ────────────────
    if args.source == "csv":
        if not args.file:
            parser.error("--file is required for CSV source")
        result = etl_from_csv_flow(
            file_path=args.file,
            output_filename=args.output,
            outliers_strategy=args.outliers,
            missing_data_strategy=args.missing,
            normalize_strategy=args.normalize,
            output_format=args.format,
            load_to_db=args.load_to_db,
            track_in_mlflow=not args.no_mlflow,
            check_schema_drift=not args.no_drift_check,
        )

    elif args.source == "excel":
        if not args.file:
            parser.error("--file is required for Excel source")
        result = etl_pipeline_flow(
            source_type="excel",
            source_config={"file_path": args.file},
            output_filename=args.output,
            outliers_strategy=args.outliers,
            missing_data_strategy=args.missing,
            normalize_strategy=args.normalize,
            output_format=args.format,
            load_to_db=args.load_to_db,
            db_type=args.db_type,
            db_uri=args.db_uri,
            track_in_mlflow=not args.no_mlflow,
            strict_gatekeeper=args.strict_gatekeeper,
            check_schema_drift=not args.no_drift_check,
        )

    elif args.source == "database":
        result = etl_from_database_flow(
            table_name=args.table,
            product_id=args.product_id,
            start_date=args.start_date,
            end_date=args.end_date,
            output_filename=args.output,
            outliers_strategy=args.outliers,
            missing_data_strategy=args.missing,
            normalize_strategy=args.normalize,
            output_format=args.format,
            load_to_db=args.load_to_db,
            db_type=args.db_type,
            db_uri=args.db_uri,
            track_in_mlflow=not args.no_mlflow,
            strict_gatekeeper=args.strict_gatekeeper,
            check_schema_drift=not args.no_drift_check,
        )

    elif args.source == "kafka":
        if not args.topic:
            parser.error("--topic is required for Kafka source")
        result = etl_from_kafka_flow(
            topic=args.topic,
            max_messages=args.max_messages,
            output_filename=args.output,
            outliers_strategy=args.outliers,
            missing_data_strategy=args.missing,
            normalize_strategy=args.normalize,
            output_format=args.format,
            load_to_db=args.load_to_db,
            db_type=args.db_type,
            db_uri=args.db_uri,
            track_in_mlflow=not args.no_mlflow,
            strict_gatekeeper=args.strict_gatekeeper,
            check_schema_drift=not args.no_drift_check,
        )

    elif args.source == "api":
        if not args.url:
            parser.error("--url is required for API source")
        result = etl_from_api_flow(
            base_url=args.url,
            endpoint=args.endpoint,
            json_path=args.json_path,
            output_filename=args.output,
            outliers_strategy=args.outliers,
            missing_data_strategy=args.missing,
            normalize_strategy=args.normalize,
            output_format=args.format,
            load_to_db=args.load_to_db,
            db_type=args.db_type,
            db_uri=args.db_uri,
            track_in_mlflow=not args.no_mlflow,
            strict_gatekeeper=args.strict_gatekeeper,
            check_schema_drift=not args.no_drift_check,
        )

    # Print final status
    status = result.get("status", "unknown")
    if status == "completed":
        print(f"\n✓ Pipeline finished successfully.")
    else:
        print(f"\n✗ Pipeline finished with status: {status}")
        error = result.get("error")
        if error:
            print(f"  Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
