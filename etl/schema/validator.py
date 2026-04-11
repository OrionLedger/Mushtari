"""
Schema validation and drift detection.

Validates a DataFrame against a known schema, and compares
two schemas to detect breaking changes between pipeline runs.
"""

from typing import Dict, List, Optional
from pathlib import Path
import json

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.schema.models import (
    DatasetSchema,
    FieldSchema,
    InferredType,
    SchemaIssue,
    IssueSeverity,
    SchemaDriftReport,
)

logger = get_logger(__name__)


# ── Schema validation ───────────────────────────────────────────────

@task(
    name="validate-schema",
    description="Validate a DataFrame against a DatasetSchema, checking "
                "that required fields exist and types are consistent.",
)
def validate_schema(
    df: pd.DataFrame,
    schema: DatasetSchema,
    strict: bool = False,
) -> List[SchemaIssue]:
    """
    Check a DataFrame against an expected DatasetSchema.

    Args:
        df:      The DataFrame to validate.
        schema:  The expected schema.
        strict:  If True, extra columns not in schema raise a WARNING.

    Returns:
        List of SchemaIssue objects found during validation.
    """
    issues: List[SchemaIssue] = []
    df_cols = set(df.columns.astype(str))
    schema_cols = set(schema.fields.keys())

    # Missing expected columns
    missing = schema_cols - df_cols
    for col in missing:
        issues.append(SchemaIssue(
            field=col,
            severity=IssueSeverity.CRITICAL,
            message=f"Expected column '{col}' is missing from the DataFrame.",
        ))

    # Extra unexpected columns
    extra = df_cols - schema_cols
    if strict and extra:
        for col in extra:
            issues.append(SchemaIssue(
                field=col,
                severity=IssueSeverity.WARNING,
                message=f"Unexpected column '{col}' found (not in schema).",
            ))

    # Type consistency for present columns
    for col_name, field_schema in schema.fields.items():
        if col_name not in df_cols:
            continue

        series = df[col_name]
        null_count = int(series.isnull().sum())

        # Check nullability
        if not field_schema.nullable and null_count > 0:
            issues.append(SchemaIssue(
                field=col_name,
                severity=IssueSeverity.WARNING,
                message=(
                    f"Column was not nullable in schema but has "
                    f"{null_count} null value(s)."
                ),
            ))

    for issue in issues:
        log_fn = (
            logger.error if issue.severity == IssueSeverity.CRITICAL
            else logger.warning
        )
        log_fn(f"[VALIDATE] {issue.field}: {issue.message}")

    return issues


# ── Schema drift detection ──────────────────────────────────────────

@task(
    name="detect-schema-drift",
    description="Compare two DatasetSchema objects and report structural "
                "changes (added/removed fields, type changes).",
)
def detect_schema_drift(
    previous: DatasetSchema,
    current: DatasetSchema,
) -> SchemaDriftReport:
    """
    Compare a previous schema to a current schema and produce a
    drift report.

    Args:
        previous: The schema from the last successful pipeline run.
        current:  The schema from the current run.

    Returns:
        A SchemaDriftReport describing all changes.
    """
    prev_fields = set(previous.fields.keys())
    curr_fields = set(current.fields.keys())

    added = sorted(curr_fields - prev_fields)
    removed = sorted(prev_fields - curr_fields)

    type_changes: Dict[str, Dict[str, str]] = {}
    nullability_changes: Dict[str, Dict[str, bool]] = {}
    details: List[str] = []

    # Compare common fields
    common = prev_fields & curr_fields
    for col in sorted(common):
        pf = previous.fields[col]
        cf = current.fields[col]

        if pf.inferred_type != cf.inferred_type:
            type_changes[col] = {
                "previous": pf.inferred_type.value,
                "current": cf.inferred_type.value,
            }
            details.append(
                f"Type change on '{col}': "
                f"{pf.inferred_type.value} → {cf.inferred_type.value}"
            )

        if pf.nullable != cf.nullable:
            nullability_changes[col] = {
                "previous": pf.nullable,
                "current": cf.nullable,
            }
            details.append(
                f"Nullability change on '{col}': "
                f"{pf.nullable} → {cf.nullable}"
            )

    for col in added:
        details.append(f"New field added: '{col}'")
    for col in removed:
        details.append(f"Field removed: '{col}'")

    has_breaking = len(removed) > 0 or len(type_changes) > 0

    report = SchemaDriftReport(
        previous_version=previous.version,
        current_version=current.version,
        added_fields=added,
        removed_fields=removed,
        type_changes=type_changes,
        nullability_changes=nullability_changes,
        has_breaking_changes=has_breaking,
        details=details,
    )

    # Log drift
    if has_breaking:
        logger.warning(
            f"[DRIFT] Breaking schema changes detected: "
            f"{len(removed)} removed, {len(type_changes)} type changes"
        )
    elif details:
        logger.info(f"[DRIFT] Non-breaking schema changes: {len(details)} change(s)")
    else:
        logger.info("[DRIFT] No schema drift detected.")

    for line in details:
        logger.info(f"  → {line}")

    return report


# ── Helper: load previous schema from disk ──────────────────────────

def load_latest_schema(source_name: str, schema_dir: Path) -> Optional[DatasetSchema]:
    """
    Load the most recent schema snapshot for a given source name.

    Returns None if no snapshot exists.
    """
    safe_name = source_name.replace("/", "_").replace(":", "_")
    candidates = sorted(schema_dir.glob(f"{safe_name}_*.json"), reverse=True)
    if not candidates:
        return None

    try:
        raw = candidates[0].read_text(encoding="utf-8")
        return DatasetSchema.model_validate_json(raw)
    except Exception as exc:
        logger.warning(f"Could not load previous schema: {exc}")
        return None
