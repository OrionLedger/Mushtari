import pandas as pd
from sklearn.metrics import mean_absolute_error

def mean_absolute_error(
        y_true:pd.Series,
        y_pred:pd.Series,
        ):
    """
    Calculates the mean absolute error between the true and predicted values.
    
    Args:
        y_true: The true values.
        y_pred: The predicted values.
    
    Returns:
        The mean absolute error.
    """
    if type(y_true) is not pd.Series or type(y_pred) is not pd.Series:
        raise ValueError("Enter valid pandas series")
    
    return mean_absolute_error(y_true, y_pred)
