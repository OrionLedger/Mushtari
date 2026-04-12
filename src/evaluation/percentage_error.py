import pandas as pd
import numpy as np

def mean_absolute_percentage_error(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Calculates the Mean Absolute Percentage Error (MAPE).
    
    Args:
        y_true: The true values.
        y_pred: The predicted values.
    
    Returns:
        The MAPE as a dynamic float (e.g. 0.15 for 15%).
    """
    if not isinstance(y_true, pd.Series) or not isinstance(y_pred, pd.Series):
        raise ValueError("Inputs must be pandas Series")
    
    # Avoid division by zero
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))
