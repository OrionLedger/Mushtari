"""
File extractors — CSV and Excel ingestion.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


# ── CSV Extractor ───────────────────────────────────────────────────

@task(
    name="extract-from-csv",
    description="Extract data from a CSV file into a DataFrame.",
)
def extract_from_csv(
    file_path: str,
    delimiter: str = ",",
    encoding: str = "utf-8",
    parse_dates: Optional[List[str]] = None,
    usecols: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read a CSV file and return a DataFrame with extraction metadata.

    Args:
        file_path:    Path to the CSV file.
        delimiter:    Column delimiter character.
        encoding:     File encoding.
        parse_dates:  List of column names to parse as datetime.
        usecols:      Subset of columns to read.

    Returns:
        (DataFrame, metadata_dict)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    logger.info(f"Extracting CSV: {path.name}")

    df = pd.read_csv(
        file_path,
        delimiter=delimiter,
        encoding=encoding,
        parse_dates=parse_dates or True,
        usecols=usecols,
    )

    metadata: Dict[str, Any] = {
        "source_type": "csv",
        "source_name": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "record_count": len(df),
        "column_count": len(df.columns),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Extracted {len(df)} rows × {len(df.columns)} cols from {path.name}")
    return df, metadata


# ── Excel Extractor ─────────────────────────────────────────────────

@task(
    name="extract-from-excel",
    description="Extract data from an Excel file into a DataFrame.",
)
def extract_from_excel(
    file_path: str,
    sheet_name: Optional[str] = None,
    usecols: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read an Excel file (.xlsx / .xls) and return a DataFrame.

    Args:
        file_path:   Path to the Excel file.
        sheet_name:  Specific sheet to read. ``None`` reads the first sheet.
        usecols:     Subset of columns to read.

    Returns:
        (DataFrame, metadata_dict)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    logger.info(f"Extracting Excel: {path.name}, sheet={sheet_name or 'first'}")

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name or 0,
        usecols=usecols,
    )

    metadata: Dict[str, Any] = {
        "source_type": "excel",
        "source_name": str(path.resolve()),
        "sheet": sheet_name or "Sheet1",
        "file_size_bytes": path.stat().st_size,
        "record_count": len(df),
        "column_count": len(df.columns),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Extracted {len(df)} rows × {len(df.columns)} cols from {path.name}")
    return df, metadata
