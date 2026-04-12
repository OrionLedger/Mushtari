"""
Data normalisation task — wraps the project's existing
``src.preprocessing.normalize_data.normalize_data``.
"""

from typing import Literal

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from src.preprocessing.normalize_data import normalize_data as _normalize_data

logger = get_logger(__name__)


@task(
    name="transform-normalize",
    description="Normalise numeric columns using standard, minmax, or "
                "robust scaling.",
)
def normalize(
    df: pd.DataFrame,
    strategy: Literal["standard", "minmax", "robust", "none"] = "none",
) -> pd.DataFrame:
    """
    Normalise numeric columns in the DataFrame.

    Args:
        df:        Input DataFrame.
        strategy:  Normalisation strategy to apply.

    Returns:
        Normalised DataFrame.
    """
    logger.info(f"Normalising data with strategy={strategy}")
    return _normalize_data(df, strategy=strategy)
