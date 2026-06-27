"""
Stub etl_flow — the full Prefect ETL pipeline is not bundled in the local build.
This stub prevents ImportError when source_registry.py references it.
"""

import logging

logger = logging.getLogger(__name__)


def etl_pipeline_flow(*args, **kwargs):
    """Stub: raises an informative error if called."""
    raise NotImplementedError(
        "The ETL pipeline is not available in this build. "
        "Use the Excel import feature instead (DataImport UI or API)."
    )
