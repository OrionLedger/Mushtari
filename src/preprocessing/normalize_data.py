import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from typing import Literal

def normalize_data(
        df:pd.DataFrame,
        strategy: Literal["standard", "minmax", "robust", "none"] = 'none',
        ):
    """
    Normalizes the dataframe using the specified strategy.
    
    Args:
        df: The dataframe to normalize.
        strategy: The strategy to use for normalization.
    
    Returns:
        The normalized dataframe.
    """
    if strategy not in ('standard', 'minmax', 'robust', 'none'):
        raise ValueError("strategy must be standard, minmax, robust, or none")

    if strategy is "standard":
        scaler = StandardScaler()
        df = scaler.fit_transform(df)
        print("Data normalized using standard scaler.")
    
    elif strategy is "minmax":
        scaler = MinMaxScaler()
        df = scaler.fit_transform(df)
        print("Data normalized using minmax scaler.")
    
    elif strategy is "robust":
        scaler = RobustScaler()
        df = scaler.fit_transform(df)
        print("Data normalized using robust scaler.")
    
    elif strategy is "none":
        print("No normalization applied.")
    
    return df