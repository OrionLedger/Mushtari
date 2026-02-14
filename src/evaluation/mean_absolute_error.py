import pandas as pd
from sklearn import metrics

def mean_absolute_error(
        y_true: pd.Series,
        y_pred: pd.Series,
        ):
    """
    Calculates the mean absolute error between the true and predicted values.
    
    Args:
        y_true: The true values.
        y_pred: The predicted values.
    
    Returns:
        The mean absolute error.
    """
    if not isinstance(y_true, pd.Series) or not isinstance(y_pred, pd.Series):
        raise ValueError("Enter valid pandas series")
    
    return metrics.mean_absolute_error(y_true, y_pred)
