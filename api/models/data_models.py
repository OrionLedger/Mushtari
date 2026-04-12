from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal

class ETLRequestPayload(BaseModel):
    source_type: Literal["database", "csv", "excel", "kafka", "api"] = Field("database", description="Data source type")
    source_config: Dict[str, Any] = Field(default_factory=dict, description="Extractor configuration specifics")
    
    # Transformation configs
    outliers_strategy: str = Field("drop", description="Outlier handling strategy")
    missing_data_strategy: str = Field("impute", description="Missing value handling strategy")
    normalize_strategy: str = Field("none", description="Normalisation strategy")
    
    # Load configs
    output_filename: Optional[str] = Field(None, description="Output file name")
    output_format: str = Field("parquet", description="Output serialization format")
    load_to_db: bool = Field(False, description="Flag to insert resulting records back into DB")
    db_type: str = Field("cassandra", description="Database target system mapping")
    db_uri: Optional[str] = Field(None, description="Destination target config URL")
    db_table_name: str = Field("processed_sales", description="Target database table")
    track_in_mlflow: bool = Field(True, description="Archive model parameters/results in MLflow natively")
    
    # Hard Gates
    strict_gatekeeper: bool = Field(False, description="Strictly halt execution on Gatekeeper validation failures")
    check_schema_drift: bool = Field(False, description="Map past footprints dynamically seeking drifts")
