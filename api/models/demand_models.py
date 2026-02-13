from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PredictPayload(BaseModel):
    product_id: int = Field(..., examples=[1])
    features: Optional[List[str]] = Field(None, examples=[["lag_1", "lag_7", "month"]])
    start_date: Optional[str] = Field(None, examples=["2026-01-01"])
    end_date: Optional[str] = Field(None, examples=["2026-02-01"])

class SalesRecord(BaseModel):
    product_id: int = Field(..., examples=[1])
    date: str = Field(..., examples=["2026-01-23"])
    sales: float = Field(..., examples=[15.5])

class SalesPayload(BaseModel):
    table_name: str = Field("Sales", examples=["Sales"])
    record: Dict[str, Any] = Field(..., examples=[{"product_id": 1, "date": "2026-01-23", "sales": 15}])

class TrainPayload(BaseModel):
    product_id: int = Field(..., examples=[1])
    columns: List[str] = Field(["sales"], examples=[["sales", "price"]])
    start_date: Optional[str] = Field(None, examples=["2025-01-01"])
    end_date: Optional[str] = Field(None, examples=["2025-12-31"])
    test_size: float = Field(0.2, examples=[0.2])