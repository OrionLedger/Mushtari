import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_market_fit_kpis(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
    """
    Calculates advanced business-oriented metrics for demand forecasting.
    
    Metrics:
    - Inventory Accuracy: Percentage of time prediction covers actual demand without excessive overstock (within 20% margin).
    - Under-prediction Rate: Frequency showing potential lost sales.
    - Over-prediction Rate: Frequency showing potential waste/storage costs.
    - Forecast Bias: Sum(y_pred) / Sum(y_true). > 1 means systematic over-prediction.
    """
    if len(y_true) == 0:
        return {}

    errors = y_pred - y_true
    
    # Bias
    bias = np.sum(y_pred) / np.sum(y_true) if np.sum(y_true) != 0 else 0
    
    # Proportions
    under_pred = np.mean(y_pred < y_true)
    over_pred = np.mean(y_pred > y_true)
    
    # Inventory Efficiency (Prediction is within [100%, 120%] of actual demand)
    inventory_accurate = np.mean((y_pred >= y_true) & (y_pred <= y_true * 1.2))
    
    return {
        "forecast_bias": float(bias),
        "under_prediction_rate": float(under_pred),
        "over_prediction_rate": float(over_pred),
        "inventory_efficiency_score": float(inventory_accurate),
        "total_actual_demand": float(np.sum(y_true)),
        "total_predicted_demand": float(np.sum(y_pred))
    }
