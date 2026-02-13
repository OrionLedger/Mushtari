import pandas as pd
from sklearn.metrics import mean_squared_error

def squared_mean_error(
        y_true:pd.Series,
        y_pred:pd.Series,
        ):
    """
    Calculates the squared mean error between the true and predicted values.
    
    Args:
        y_true: The true values.
        y_pred: The predicted values.
    
    Returns:
        The squared mean error.
    """
    if type(y_true) is not pd.Series or type(y_pred) is not pd.Series:
        raise ValueError("Enter valid pandas series")
    
    return mean_squared_error(y_true, y_pred)
