"""
File loaders — write processed data to Parquet or CSV.
"""

from typing import Optional
from datetime import datetime
from pathlib import Path

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings

logger = get_logger(__name__)


@task(
    name="load-to-parquet",
    retries=2,
    retry_delay_seconds=5,
    description="Save a DataFrame to a Parquet file in the processed data directory.",
)
def load_to_parquet(
    df: pd.DataFrame,
    filename: Optional[str] = None,
    output_dir: Optional[str] = None,
    partition_by: Optional[str] = None,
) -> str:
    """
    Write a DataFrame to a Parquet file.

    Args:
        df:            The DataFrame to save.
        filename:      Output filename (without extension). If None, a
                       timestamped name is generated.
        output_dir:    Override the default output directory.
        partition_by:  Column name to partition by (creates subdirectories).

    Returns:
        Absolute path to the written file or directory.
    """
    settings = get_settings().load
    out_dir = Path(output_dir) if output_dir else settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_{ts}"

    if partition_by and partition_by in df.columns:
        out_path = out_dir / filename
        df.to_parquet(
            out_path,
            engine="pyarrow",
            partition_cols=[partition_by],
            index=False,
        )
        logger.info(
            f"Saved {len(df)} rows to partitioned Parquet: "
            f"{out_path} (by '{partition_by}')"
        )
    else:
        out_path = out_dir / f"{filename}.parquet"
        df.to_parquet(out_path, engine="pyarrow", index=False)
        logger.info(f"Saved {len(df)} rows to {out_path}")

    return str(out_path.resolve())


@task(
    name="load-to-csv",
    retries=2,
    retry_delay_seconds=5,
    description="Save a DataFrame to a CSV file in the processed data directory.",
)
def load_to_csv(
    df: pd.DataFrame,
    filename: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> str:
    """
    Write a DataFrame to a CSV file.

    Args:
        df:          The DataFrame to save.
        filename:    Output filename (without extension).
        output_dir:  Override the default output directory.

    Returns:
        Absolute path to the written file.
    """
    settings = get_settings().load
    out_dir = Path(output_dir) if output_dir else settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_{ts}"

    out_path = out_dir / f"{filename}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")

    logger.info(f"Saved {len(df)} rows to {out_path}")
    return str(out_path.resolve())
