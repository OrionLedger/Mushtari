import pandas as pd
from sklearn import metrics

def squared_mean_error(
        y_true: pd.Series,
        y_pred: pd.Series,
        ):
    """
    Calculates the squared mean error between the true and predicted values.
    
    Args:
        y_true: The true values.
        y_pred: The predicted values.
    
    Returns:
        The squared mean error.
    """
    if not isinstance(y_true, pd.Series) or not isinstance(y_pred, pd.Series):
        raise ValueError("Enter valid pandas series")
    
    return metrics.mean_squared_error(y_true, y_pred)
