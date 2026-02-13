import numpy as np

def naive_forecast(train, steps):
    """
    Generates a naive forecast.
    
    Args:
        train: The training data.
        steps: The number of steps to forecast.
    
    Returns:
        The forecast.
    """
    return np.repeat(train.iloc[-1], steps)
