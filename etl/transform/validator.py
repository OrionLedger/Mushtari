"""
Data validation task — checks data quality after transformation.

Validates row counts, null ratios, and duplicate presence.
"""

from typing import List

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings
from etl.schema.models import DatasetSchema

logger = get_logger(__name__)


@task(
    name="transform-validate",
    description="Validate the transformed DataFrame: check row counts, "
                "null ratios, and duplicates.",
)
def validate_data(
    df: pd.DataFrame,
    schema: DatasetSchema,
    min_rows: int | None = None,
    max_null_ratio: float | None = None,
    fail_on_error: bool = True,
) -> pd.DataFrame:
    """
    Run data quality checks on the transformed DataFrame.

    Args:
        df:             The DataFrame to validate.
        schema:         The DatasetSchema for context.
        min_rows:       Minimum number of rows required. Uses config default if None.
        max_null_ratio: Maximum allowed null ratio per column. Uses config default if None.
        fail_on_error:  If True, raise ValueError on validation failure.

    Returns:
        The same DataFrame (passthrough on success).

    Raises:
        ValueError: If any validation check fails and ``fail_on_error`` is True.
    """
    settings = get_settings().transform
    min_rows = min_rows if min_rows is not None else settings.min_rows_required
    max_null_ratio = (
        max_null_ratio if max_null_ratio is not None
        else settings.max_null_ratio
    )

    errors: List[str] = []
    warnings: List[str] = []

    # ── Row count ───────────────────────────────────────────────
    if len(df) < min_rows:
        errors.append(
            f"Row count ({len(df)}) is below minimum ({min_rows})."
        )

    if len(df) == 0:
        errors.append("DataFrame is empty after transformation.")
        if fail_on_error:
            raise ValueError(" | ".join(errors))
        return df

    # ── Null ratios ─────────────────────────────────────────────
    for col in df.columns:
        null_ratio = df[col].isnull().mean()
        if null_ratio > max_null_ratio:
            msg = (
                f"Column '{col}' has {null_ratio:.1%} nulls "
                f"(threshold: {max_null_ratio:.1%})."
            )
            if null_ratio > 0.9:
                errors.append(msg)
            else:
                warnings.append(msg)

    # ── Duplicate rows ──────────────────────────────────────────
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        dup_pct = dup_count / len(df)
        msg = f"{dup_count} duplicate rows ({dup_pct:.1%} of data)."
        if dup_pct > 0.5:
            errors.append(msg)
        else:
            warnings.append(msg)

    # ── Log results ─────────────────────────────────────────────
    for w in warnings:
        logger.warning(f"[VALIDATE] {w}")
    for e in errors:
        logger.error(f"[VALIDATE] {e}")

    if not errors and not warnings:
        logger.info(
            f"[VALIDATE] All checks passed: {len(df)} rows, "
            f"{len(df.columns)} columns."
        )

    if errors and fail_on_error:
        raise ValueError(
            f"Data validation failed with {len(errors)} error(s): "
            + " | ".join(errors)
        )

    return df
