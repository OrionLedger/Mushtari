"""
Schema Identifier — the core engine of the ETL schema step.

Automatically infers schema from a pandas DataFrame by analysing:
  • Column data types (maps pandas dtypes to canonical InferredType)
  • Nullability and null ratios
  • Cardinality / uniqueness
  • Nested structures (JSON-encoded strings, dicts, lists)
  • Common patterns (dates, UUIDs, emails)
  • Type consistency within mixed-type object columns

Outputs a ``DatasetSchema`` Pydantic model that downstream Transform
and Load steps consume.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
import re

import numpy as np
import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings
from etl.schema.models import (
    DatasetSchema,
    FieldSchema,
    InferredType,
    SchemaIssue,
    IssueSeverity,
)

logger = get_logger(__name__)

# ── Pattern detectors ───────────────────────────────────────────────

_ISO_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?",
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")


def _detect_pattern(values: pd.Series) -> Optional[str]:
    """Try to detect a common pattern in string values."""
    sample = values.dropna().head(50).astype(str)
    if sample.empty:
        return None

    if sample.apply(lambda v: bool(_ISO_DATE_RE.match(v))).mean() > 0.8:
        return "ISO-8601"
    if sample.apply(lambda v: bool(_UUID_RE.match(v))).mean() > 0.8:
        return "UUID"
    if sample.apply(lambda v: bool(_EMAIL_RE.match(v))).mean() > 0.8:
        return "email"
    return None


# ── Nested structure detection ──────────────────────────────────────

def _try_parse_json(value: Any) -> Optional[Any]:
    """Attempt to parse a value as JSON.  Returns parsed obj or None."""
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
        if isinstance(parsed, (dict, list)):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _detect_nested(series: pd.Series, sample_size: int = 100) -> tuple[bool, Optional[List[str]]]:
    """
    Check whether a column contains nested structures
    (JSON strings, dicts, or lists).

    Returns:
        (is_nested, list_of_keys_if_dict_or_None)
    """
    sample = series.dropna().head(sample_size)
    if sample.empty:
        return False, None

    # Already dict/list objects (e.g. from API/Kafka JSON ingestion)
    native_complex = sample.apply(lambda v: isinstance(v, (dict, list)))
    if native_complex.mean() > 0.5:
        dict_items = sample[sample.apply(lambda v: isinstance(v, dict))]
        if not dict_items.empty:
            keys = set()
            for d in dict_items:
                keys.update(d.keys())
            return True, sorted(keys)
        return True, None

    # JSON-encoded strings
    parsed = sample.apply(_try_parse_json)
    json_ratio = parsed.notna().mean()
    if json_ratio > 0.5:
        dict_items = parsed[parsed.apply(lambda v: isinstance(v, dict))]
        if not dict_items.empty:
            keys = set()
            for d in dict_items.dropna():
                keys.update(d.keys())
            return True, sorted(keys)
        return True, None

    return False, None


# ── Type inference ──────────────────────────────────────────────────

def _infer_type(series: pd.Series) -> InferredType:
    """Map a pandas Series to a canonical InferredType."""
    dtype = series.dtype

    # Numeric types
    if pd.api.types.is_bool_dtype(dtype):
        return InferredType.BOOLEAN
    if pd.api.types.is_integer_dtype(dtype):
        return InferredType.INTEGER
    if pd.api.types.is_float_dtype(dtype):
        # Check if all non-null values are actually integer-valued floats
        non_null = series.dropna()
        if not non_null.empty and (non_null == non_null.astype(int)).all():
            return InferredType.INTEGER
        return InferredType.FLOAT

    # Datetime
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return InferredType.DATETIME

    # Object columns — need deeper inspection
    if dtype == object:
        non_null = series.dropna()
        if non_null.empty:
            return InferredType.UNKNOWN

        # Sample for type distribution
        type_counts: Dict[str, int] = {}
        for val in non_null.head(200):
            t = type(val).__name__
            type_counts[t] = type_counts.get(t, 0) + 1

        dominant_type = max(type_counts, key=type_counts.get)
        total = sum(type_counts.values())
        dominant_ratio = type_counts[dominant_type] / total

        if dominant_ratio < 0.8 and len(type_counts) > 1:
            return InferredType.MIXED

        if dominant_type == "dict":
            return InferredType.JSON
        if dominant_type == "list":
            return InferredType.LIST
        if dominant_type == "bool":
            return InferredType.BOOLEAN

        # String column — check if it's actually dates or JSON
        if dominant_type == "str":
            # Check for JSON strings
            json_ratio = non_null.head(100).apply(
                lambda v: _try_parse_json(v) is not None
            ).mean()
            if json_ratio > 0.5:
                return InferredType.JSON

            # Check for date strings
            pattern = _detect_pattern(non_null)
            if pattern == "ISO-8601":
                return InferredType.DATETIME

            return InferredType.STRING

        # Fallback for int/float stored as object
        if dominant_type in ("int", "int64"):
            return InferredType.INTEGER
        if dominant_type in ("float", "float64"):
            return InferredType.FLOAT

    # Categorical
    if pd.api.types.is_categorical_dtype(dtype):
        return InferredType.STRING

    return InferredType.UNKNOWN


# ── Main identification function ────────────────────────────────────

def _build_field_schema(
    name: str,
    series: pd.Series,
    total_rows: int,
    settings,
) -> tuple[FieldSchema, List[SchemaIssue]]:
    """Analyse a single column and produce a FieldSchema + issues."""
    issues: List[SchemaIssue] = []

    null_count = int(series.isnull().sum())
    null_pct = null_count / total_rows if total_rows > 0 else 0.0
    unique_count = int(series.nunique(dropna=True))
    cardinality = unique_count / total_rows if total_rows > 0 else 0.0

    # Infer type
    inferred_type = _infer_type(series)

    # Detect nested structures
    is_nested, nested_keys = _detect_nested(
        series, sample_size=settings.nested_detection_sample
    )
    if is_nested and inferred_type == InferredType.STRING:
        inferred_type = InferredType.JSON

    # Detect pattern
    pattern = None
    if inferred_type == InferredType.STRING:
        pattern = _detect_pattern(series)

    # Min/max for numeric and datetime
    min_val = None
    max_val = None
    if inferred_type in (InferredType.INTEGER, InferredType.FLOAT):
        non_null = pd.to_numeric(series, errors="coerce").dropna()
        if not non_null.empty:
            min_val = float(non_null.min())
            max_val = float(non_null.max())
    elif inferred_type in (InferredType.DATETIME, InferredType.DATE):
        try:
            dt = pd.to_datetime(series, errors="coerce").dropna()
            if not dt.empty:
                min_val = dt.min().isoformat()
                max_val = dt.max().isoformat()
        except Exception:
            pass

    # Sample values (up to 5, JSON-serialisable)
    sample_values = []
    for v in series.dropna().head(5):
        try:
            json.dumps(v, default=str)
            sample_values.append(v)
        except (TypeError, ValueError):
            sample_values.append(str(v))

    # ── Issue detection ─────────────────────────────────────────
    if null_pct >= settings.null_threshold_critical:
        issues.append(SchemaIssue(
            field=name,
            severity=IssueSeverity.CRITICAL,
            message=f"Column has {null_pct:.0%} null values — nearly empty.",
        ))
    elif null_pct >= settings.null_threshold_warning:
        issues.append(SchemaIssue(
            field=name,
            severity=IssueSeverity.WARNING,
            message=f"Column has {null_pct:.0%} null values.",
        ))

    if inferred_type == InferredType.MIXED:
        issues.append(SchemaIssue(
            field=name,
            severity=IssueSeverity.WARNING,
            message="Column contains mixed data types.",
        ))

    if inferred_type == InferredType.UNKNOWN:
        issues.append(SchemaIssue(
            field=name,
            severity=IssueSeverity.WARNING,
            message="Could not determine data type for this column.",
        ))

    field = FieldSchema(
        name=name,
        inferred_type=inferred_type,
        original_dtype=str(series.dtype),
        nullable=null_count > 0,
        null_count=null_count,
        null_percentage=round(null_pct, 4),
        unique_count=unique_count,
        cardinality_ratio=round(cardinality, 4),
        min_value=min_val,
        max_value=max_val,
        sample_values=sample_values,
        is_nested=is_nested,
        nested_keys=nested_keys,
        detected_pattern=pattern,
    )

    return field, issues


# ── Prefect task ────────────────────────────────────────────────────

@task(
    name="identify-schema",
    description="Automatically infer schema from a DataFrame: field names, "
                "data types, nested structures, null ratios, patterns, "
                "and data quality issues.",
)
def identify_schema(
    df: pd.DataFrame,
    source_name: str = "unknown",
    source_type: str = "unknown",
) -> DatasetSchema:
    """
    Analyse a DataFrame and produce a standardised ``DatasetSchema``.

    Steps performed:
        1. Iterate over every column.
        2. Infer canonical type (int, float, str, bool, datetime, json, list, mixed).
        3. Detect nested structures (dict / JSON strings) and extract keys.
        4. Detect common patterns (ISO-8601, UUID, email).
        5. Compute null counts, cardinality, min/max, samples.
        6. Flag quality issues (high nulls, mixed types, unknown types).
        7. Return a fully populated DatasetSchema.

    Args:
        df:          The DataFrame to analyse.
        source_name: Human-readable name of the data source.
        source_type: Source category ("database", "csv", "kafka", "api").

    Returns:
        A DatasetSchema Pydantic model.
    """
    settings = get_settings().schema
    total_rows = len(df)
    all_issues: List[SchemaIssue] = []
    fields: Dict[str, FieldSchema] = {}

    logger.info(
        f"Identifying schema for '{source_name}' — "
        f"{total_rows} rows × {len(df.columns)} columns"
    )

    if df.empty:
        all_issues.append(SchemaIssue(
            severity=IssueSeverity.CRITICAL,
            message="DataFrame is empty — no data to infer schema from.",
        ))
        return DatasetSchema(
            source_name=source_name,
            source_type=source_type,
            record_count=0,
            field_count=0,
            fields={},
            issues=all_issues,
        )

    for col_name in df.columns:
        field_schema, field_issues = _build_field_schema(
            name=str(col_name),
            series=df[col_name],
            total_rows=total_rows,
            settings=settings,
        )
        fields[str(col_name)] = field_schema
        all_issues.extend(field_issues)

    schema = DatasetSchema(
        source_name=source_name,
        source_type=source_type,
        record_count=total_rows,
        field_count=len(fields),
        fields=fields,
        inferred_at=datetime.now(timezone.utc),
        issues=all_issues,
    )

    # ── Log summary ─────────────────────────────────────────────
    logger.info(schema.summary())
    for issue in all_issues:
        if issue.severity == IssueSeverity.CRITICAL:
            logger.error(f"[SCHEMA] {issue.field or 'GLOBAL'}: {issue.message}")
        elif issue.severity == IssueSeverity.WARNING:
            logger.warning(f"[SCHEMA] {issue.field or 'GLOBAL'}: {issue.message}")
        else:
            logger.info(f"[SCHEMA] {issue.field or 'GLOBAL'}: {issue.message}")

    # ── Persist schema snapshot ─────────────────────────────────
    try:
        schema_dir = settings.schema_history_dir
        schema_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = source_name.replace("/", "_").replace(":", "_")
        path = schema_dir / f"{safe_name}_{ts}.json"
        path.write_text(schema.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Schema snapshot saved to {path}")
    except Exception as exc:
        logger.warning(f"Could not persist schema snapshot: {exc}")

    return schema
