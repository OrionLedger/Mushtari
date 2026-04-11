from typing import Any, Dict, Optional
import pandas as pd
from prefect import task
from infrastructure.logging.logger import get_logger
from etl.gatekeeper.schemas import get_schema
import pandera as pa

logger = get_logger(__name__)

@task(name="gatekeeper-validation")
def apply_gatekeeper_rules(df: pd.DataFrame, schema_name: str = "sales", strict_halt: bool = True) -> pd.DataFrame:
    """
    Apply strict Pandera business rules.
    If strict_halt is True, raises an error and halts the specific flow.
    If False, it will attempt to drop the heavily invalid rows and return a clean subset.
    """
    logger.info(f"Applying strict Gatekeeper validation using '{schema_name}' baseline rules.")
    
    pandera_schema = get_schema(schema_name)
    
    if df.empty:
        return df

    try:
        # We try to validate natively
        validated_df = pandera_schema.validate(df, lazy=True)
        return validated_df
    except pa.errors.SchemaErrors as err:
        logger.warning(f"Gatekeeper found {len(err.failure_cases)} schema/rule violations!")
        
        if strict_halt:
            logger.error("strict_halt is enabled. Pipeline will be aborted to prevent corruption.")
            raise ValueError(f"Gatekeeper aborted flow due to strict schema violations:\n{err.failure_cases.head()}")
        
        # If not strict_halt, drop the rows identified in the error cases.
        logger.warning("strict_halt is False. Dropping invalid rows intelligently based on failures.")
        
        # Extract indices of failure cases
        invalid_indices = err.failure_cases['index'].dropna().unique()
        
        if len(invalid_indices) > 0:
            df_clean = df.drop(index=invalid_indices)
            logger.info(f"Dropped {len(invalid_indices)} corrupted rows. {len(df_clean)} remain valid.")
            return df_clean
        else:
            return df
