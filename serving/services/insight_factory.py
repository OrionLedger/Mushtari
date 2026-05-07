from typing import List, Dict, Any, Optional
from repo import get_repository
from etl.config.settings import get_settings
import uuid

class InsightFactory:
    """
    Service for archiving and retrieving AI Insights and generated Reports.
    Bridges the automated BI engine with the persistent relational layer.
    """

    @staticmethod
    def _get_repo():
        return get_repository("postgres")

    @classmethod
    def archive_insight(cls, insight_data: Dict[str, Any]) -> bool:
        """
        Persists a new AI observation with its associated visual (IRS) blueprint.
        """
        repo = cls._get_repo()
        return repo.add_record("insights", insight_data)

    @classmethod
    def get_library_insights(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves archived observations from the Insights Library.
        """
        repo = cls._get_repo()
        filters = {}
        if category and category != 'All':
            filters["category"] = category
            
        return repo.get_record("insights", filters=filters)

    @classmethod
    def register_report(cls, report_meta: Dict[str, Any]) -> bool:
        """
        Records a newly generated report (PDF/Excel) in the document registry.
        """
        repo = cls._get_repo()
        return repo.add_record("reports", report_meta)

    @classmethod
    def get_historical_reports(cls) -> List[Dict[str, Any]]:
        """
        Retrieves all archived documents for auditing.
        """
        repo = cls._get_repo()
        return repo.get_record("reports")

    @classmethod
    def delete_insight(cls, insight_id: int) -> bool:
        """
        Removes an observation from the library.
        """
        repo = cls._get_repo()
        return repo.delete_record("insights", insight_id)
    @classmethod
    def delete_report(cls, report_id: int) -> bool:
        """
        Removes a report from the registry.
        """
        repo = cls._get_repo()
        return repo.delete_record("reports", report_id)
