"""
Data cleaning task — wraps the project's existing
``src.preprocessing.clean_data.clean_data`` with Prefect and logging.
"""

from typing import Literal

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from src.preprocessing.clean_data import clean_data as _clean_data

logger = get_logger(__name__)


@task(
    name="transform-clean",
    description="Clean the DataFrame: handle missing values and outliers "
                "using the project's existing preprocessing module.",
)
def clean(
    df: pd.DataFrame,
    outliers_strategy: Literal["drop", "stl_dec", "rolling", "hampel"] = "drop",
    missing_data: Literal["drop", "impute", "none"] = "impute",
) -> pd.DataFrame:
    """
    Clean the DataFrame using the existing preprocessing logic.

    Args:
        df:                 Input DataFrame.
        outliers_strategy:  Strategy for outlier removal.
        missing_data:       Strategy for missing value handling.

    Returns:
        Cleaned DataFrame.
    """
    rows_before = len(df)
    nulls_before = int(df.isnull().sum().sum())

    logger.info(
        f"Cleaning data: {rows_before} rows, {nulls_before} total nulls, "
        f"outliers={outliers_strategy}, missing={missing_data}"
    )

    df_cleaned = _clean_data(
        df,
        outliers_strategy=outliers_strategy,
        missing_data=missing_data,
    )

    rows_after = len(df_cleaned)
    nulls_after = int(df_cleaned.isnull().sum().sum())

    logger.info(
        f"Cleaning complete: {rows_before}→{rows_after} rows, "
        f"{nulls_before}→{nulls_after} nulls"
    )

    return df_cleaned
