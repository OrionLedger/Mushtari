"""
Moshtari ETL Pipeline
=====================
A modular ETL pipeline built with Prefect for the Moshtari demand forecasting platform.

Modules:
    - extract:   Data ingestion from Database, CSV/Excel, Kafka, and APIs
    - schema:    Automatic schema inference, validation, and drift detection
    - transform: Data cleaning, normalisation, type casting, and validation
    - load:      Output to Database, Parquet files, and MLflow
    - flows:     Prefect flow definitions orchestrating the full pipeline
    - config:    Pipeline settings and configuration
"""
