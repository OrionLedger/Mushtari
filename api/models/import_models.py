from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class ImportResponse(BaseModel):
    status: str = Field(..., description="completed, error")
    message: Optional[str] = Field(None, description="Error message if status is error")
    total_rows: int = Field(0, description="Total rows in the file")
    rows_imported: int = Field(0, description="Rows successfully imported")
    rows_updated: int = Field(0, description="Rows updated (products only)")
    rows_failed: int = Field(0, description="Rows that failed to import")
    rows_skipped: int = Field(0, description="Rows skipped due to missing required data")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages")
    duration_ms: float = Field(0.0, description="Processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "total_rows": 50,
                "rows_imported": 48,
                "rows_updated": 2,
                "rows_failed": 0,
                "rows_skipped": 0,
                "errors": [],
                "warnings": ["Row 12: invalid weight 'abc', using 0"],
                "duration_ms": 1250.5,
            }
        }


class TemplateResponse(BaseModel):
    status: str = "ok"
    message: str = "Template generated"
    download_url: str = Field(..., description="URL to download the template file")
    description: str = Field(..., description="Description of the Excel template columns")
    expected_columns: Dict[str, List[str]] = Field(..., description="Expected columns (required/optional)")
