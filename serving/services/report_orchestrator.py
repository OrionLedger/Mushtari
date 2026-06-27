"""
serving/services/report_orchestrator.py

Orchestrates the generation and archival of business reports.
Exports data from the fact-stores and registers the manifest in PostgreSQL.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
from infrastructure.logging.logger import get_logger
from repo.current import get_active_repository

logger = get_logger(__name__)


class ReportOrchestrator:
    @staticmethod
    def _get_repo():
        """Return the configured repository from the single injection point."""
        return get_active_repository()

    @classmethod
    def generate_sales_audit(cls, format: str = "CSV") -> Optional[str]:
        """
        Generates a comprehensive sales audit report.
        """
        logger.info(f"Generating Sales Audit Report (Format: {format})...")

        try:
            repo = cls._get_repo()
            rows = repo.get_record("sales")
            if not rows:
                logger.warning("No sales data found for report.")
                return None

            df = pd.DataFrame(rows)

            # Create reports directory if it doesn't exist
            reports_dir = Path("data/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)

            filename = f"sales_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format.lower()}"
            filepath = reports_dir / filename

            if format.upper() == "CSV":
                df.to_csv(filepath, index=False)
            elif format.upper() == "JSON":
                df.to_json(filepath, orient="records")
            else:
                return None

            # Register in PostgreSQL
            cls._register_report(
                name=f"Sales Audit {datetime.now().strftime('%Y-%m-%d')}",
                report_type=format.upper(),
                file_path=str(filepath),
                file_size_kb=int(os.path.getsize(filepath) / 1024)
            )

            logger.info(f"Report generated and registered: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return None

    @classmethod
    def _register_report(cls, name: str, report_type: str, file_path: str, file_size_kb: int):
        repo = cls._get_repo()
        try:
            repo.add_record("reports", {
                "name": name,
                "report_type": report_type,
                "file_path": file_path,
                "file_size_kb": file_size_kb
            })
        except Exception as e:
            logger.error(f"Failed to register report in SQL: {e}")
