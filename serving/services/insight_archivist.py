"""
serving/services/insight_archivist.py

Bridges the AI Analyst workbench with the persistent relational library.
Archivates machine-generated observations into PostgreSQL for human review.
"""

import json
from typing import Dict, Any, Optional
from infrastructure.logging.logger import get_logger
from repo import get_repository
from etl.config.settings import get_settings

logger = get_logger(__name__)

class InsightArchivist:
    @staticmethod
    def _get_postgres():
        settings = get_settings().extract.postgres
        return get_repository("postgres", **vars(settings))

    @classmethod
    def archive_insight(cls, insight_data: Dict[str, Any]) -> bool:
        """
        Saves a generated insight into the relational library.
        
        Expected fields: title, category, impact, description, visual_schema
        """
        repo = cls._get_postgres()
        
        record = {
            "title": insight_data.get("title", "Untitled Insight"),
            "category": insight_data.get("category", "General"),
            "impact": insight_data.get("impact", "low"),
            "description": insight_data.get("description", ""),
            # Map visual blueprint to PostgreSQL JSONB
            "visual_schema": insight_data.get("visual_schema", {})
        }

        try:
            with repo:
                repo.add_record("insights", record)
                logger.info(f"✓ Insight '{record['title']}' archived to library.")
                return True
        except Exception as e:
            logger.error(f"Failed to archive insight: {e}")
            return False

def save_to_library(insight: Dict[str, Any]):
    """Public wrapper for insight archival."""
    return InsightArchivist.archive_insight(insight)
