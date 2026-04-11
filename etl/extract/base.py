"""
Base extractor interface.
All concrete extractors follow this contract.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class BaseExtractor(ABC):
    """
    Abstract base class for all data extractors.

    Every extractor must implement ``extract()`` which returns a pandas
    DataFrame and an optional metadata dict describing the source.
    """

    @abstractmethod
    def extract(self, **kwargs) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Perform the extraction.

        Returns:
            A tuple of (DataFrame, metadata_dict).
            metadata_dict should contain keys like:
                - source_type: str  ("database", "csv", "kafka", "api")
                - source_name: str  (table name, file path, topic, URL)
                - record_count: int
                - extracted_at: str (ISO timestamp)
        """
        ...

    @abstractmethod
    def validate_connection(self) -> bool:
        """Check that the data source is reachable."""
        ...
