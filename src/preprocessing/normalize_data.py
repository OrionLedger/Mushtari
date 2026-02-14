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

    if strategy == "standard":
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df)
        df = pd.DataFrame(df_scaled, columns=df.columns, index=df.index)
        print("Data normalized using standard scaler.")
    
    elif strategy == "minmax":
        scaler = MinMaxScaler()
        df_scaled = scaler.fit_transform(df)
        df = pd.DataFrame(df_scaled, columns=df.columns, index=df.index)
        print("Data normalized using minmax scaler.")
    
    elif strategy == "robust":
        scaler = RobustScaler()
        df_scaled = scaler.fit_transform(df)
        df = pd.DataFrame(df_scaled, columns=df.columns, index=df.index)
        print("Data normalized using robust scaler.")
    
    elif strategy == "none":
        print("No normalization applied.")
    
    return df