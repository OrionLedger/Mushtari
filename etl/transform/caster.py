"""
Type casting task — casts DataFrame columns to the types declared
in a DatasetSchema, handling conversion errors gracefully.
"""

from typing import Dict, List

import numpy as np
import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.schema.models import DatasetSchema, InferredType

logger = get_logger(__name__)

# Mapping from InferredType to pandas-compatible casting targets
_CAST_MAP: Dict[InferredType, str] = {
    InferredType.INTEGER:  "Int64",        # nullable integer
    InferredType.FLOAT:    "float64",
    InferredType.STRING:   "string",
    InferredType.BOOLEAN:  "boolean",      # nullable boolean
    InferredType.DATETIME: "datetime64[ns]",
}


@task(
    name="transform-cast-types",
    description="Cast DataFrame columns to the types declared in the "
                "inferred schema. Handles conversion errors per-cell.",
)
def cast_types(
    df: pd.DataFrame,
    schema: DatasetSchema,
    errors: str = "coerce",
) -> pd.DataFrame:
    """
    Cast each column in the DataFrame to match the schema's inferred type.

    Args:
        df:      Input DataFrame.
        schema:  The DatasetSchema from the identify_schema step.
        errors:  How to handle casting errors:
                 ``"coerce"`` → set failed casts to NaN/NaT
                 ``"raise"``  → raise on first failure

    Returns:
        DataFrame with columns cast to their declared types.
    """
    df = df.copy()
    cast_log: List[str] = []
    error_log: List[str] = []

    for col_name, field in schema.fields.items():
        if col_name not in df.columns:
            continue

        target_type = field.inferred_type

        # Skip types that don't need / can't be simply cast
        if target_type in (
            InferredType.JSON,
            InferredType.LIST,
            InferredType.MIXED,
            InferredType.UNKNOWN,
        ):
            logger.debug(f"Skipping cast for '{col_name}' (type={target_type.value})")
            continue

        pandas_dtype = _CAST_MAP.get(target_type)
        if pandas_dtype is None:
            continue

        try:
            if target_type == InferredType.DATETIME:
                df[col_name] = pd.to_datetime(df[col_name], errors=errors)
            elif target_type == InferredType.INTEGER:
                # Convert through float first to handle "1.0" strings
                numeric = pd.to_numeric(df[col_name], errors=errors)
                df[col_name] = numeric.astype("Int64")
            elif target_type == InferredType.FLOAT:
                df[col_name] = pd.to_numeric(df[col_name], errors=errors)
            elif target_type == InferredType.BOOLEAN:
                df[col_name] = df[col_name].astype("boolean")
            elif target_type == InferredType.STRING:
                df[col_name] = df[col_name].astype("string")

            cast_log.append(f"{col_name} → {pandas_dtype}")

        except Exception as exc:
            msg = f"Failed to cast '{col_name}' to {pandas_dtype}: {exc}"
            error_log.append(msg)
            if errors == "raise":
                raise TypeError(msg) from exc
            logger.warning(msg)

    if cast_log:
        logger.info(f"Type casting applied: {', '.join(cast_log)}")
    if error_log:
        logger.warning(f"Type casting errors: {len(error_log)}")

    return df
