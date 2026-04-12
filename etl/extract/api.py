"""
External API extractor — fetches data from REST APIs.

Uses ``httpx`` (already in requirements.txt) for HTTP requests.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pandas as pd
import httpx
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings

logger = get_logger(__name__)


class APIExtractor:
    """
    Fetch data from an external REST API endpoint and normalise
    the JSON response into a DataFrame.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ):
        settings = get_settings().extract
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout or settings.api_timeout_seconds
        self.max_retries = settings.api_max_retries

    def validate_connection(self) -> bool:
        """Send a lightweight HEAD/GET to verify the endpoint is alive."""
        try:
            resp = httpx.head(self.base_url, headers=self.headers, timeout=5)
            return resp.status_code < 500
        except Exception as exc:
            logger.error(f"API connection check failed: {exc}")
            return False

    def extract(
        self,
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        json_path: Optional[str] = None,
        paginate: bool = False,
        page_param: str = "page",
        max_pages: int = 50,
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Fetch JSON data from the API and return a DataFrame.

        Args:
            endpoint:   Path appended to base_url (e.g. ``/data/sales``).
            params:     Query parameters dict.
            method:     HTTP method (GET or POST).
            json_path:  Dot-notation path to the array in the response
                        (e.g. ``"data.results"``). If None, the response
                        root is used.
            paginate:   If True, auto-paginate using ``page_param``.
            page_param: Query parameter name for pagination.
            max_pages:  Safety limit for total pages.

        Returns:
            (DataFrame, metadata_dict)
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        params = params or {}
        all_records: List[Dict[str, Any]] = []
        pages_fetched = 0

        logger.info(f"Extracting from API: {method} {url}")

        with httpx.Client(
            headers=self.headers,
            timeout=self.timeout,
        ) as client:
            while True:
                pages_fetched += 1

                if method.upper() == "GET":
                    resp = client.get(url, params=params)
                else:
                    resp = client.post(url, json=params)

                resp.raise_for_status()
                data = resp.json()

                # Navigate to nested array if json_path provided
                if json_path:
                    for key in json_path.split("."):
                        data = data[key]

                if isinstance(data, list):
                    all_records.extend(data)
                elif isinstance(data, dict):
                    all_records.append(data)

                # Pagination
                if not paginate or pages_fetched >= max_pages:
                    break

                # Check if more pages exist (empty page = stop)
                if isinstance(data, list) and len(data) == 0:
                    break

                params[page_param] = pages_fetched + 1

        df = pd.json_normalize(all_records)

        metadata: Dict[str, Any] = {
            "source_type": "api",
            "source_name": url,
            "record_count": len(df),
            "pages_fetched": pages_fetched,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Extracted {len(df)} records from API "
            f"({pages_fetched} page(s))"
        )
        return df, metadata


# ── Prefect task wrapper ────────────────────────────────────────────

@task(
    name="extract-from-api",
    retries=3,
    retry_delay_seconds=10,
    description="Fetch data from an external REST API.",
)
def extract_from_api(
    base_url: str,
    endpoint: str = "",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
    json_path: Optional[str] = None,
    paginate: bool = False,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Prefect task: extract data from a REST API."""
    extractor = APIExtractor(base_url=base_url, headers=headers)
    return extractor.extract(
        endpoint=endpoint,
        params=params,
        method=method,
        json_path=json_path,
        paginate=paginate,
    )
