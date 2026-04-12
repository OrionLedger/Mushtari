from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from src.evaluation.market_fit import calculate_market_fit_kpis

router = APIRouter(prefix="/api/kpi", tags=["KPIs"])

class KPIRequest(BaseModel):
    actuals: List[float] = Field(..., examples=[[10.0, 15.0, 12.0]])
    predictions: List[float] = Field(..., examples=[[11.0, 14.5, 13.0]])

@router.post("/market-fit")
async def get_market_fit_metrics(payload: KPIRequest):
    """
    Calculate Market Fit KPIs (Bias, Inventory Efficiency, etc.) based on arrays of actuals and predictions.
    """
    if len(payload.actuals) != len(payload.predictions):
        raise HTTPException(status_code=400, detail="Actuals and predictions must have the same length.")
    
    y_true = pd.Series(payload.actuals)
    y_pred = pd.Series(payload.predictions)
    
    kpis = calculate_market_fit_kpis(y_true, y_pred)
    return kpis
