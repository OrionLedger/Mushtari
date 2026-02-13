import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from typing import Literal

def clean_data(
        df:pd.DataFrame,
        outliers_strategy: Literal["drop", "stl_dec", "rolling", "hampel"],
        missing_data: Literal["drop", "impute", "none"] = 'none',
        ):
    """
    Cleans the dataframe by removing outliers and missing values.
    
    Args:
        df: The dataframe to clean.
        outliers_strategy: The strategy to use for removing outliers.
        missing_data: The strategy to use for removing missing values.
    
    Returns:
        The cleaned dataframe.
    """
    if missing_data not in ('impute', 'drop'):
        raise ValueError("missing_data must be impute, drop, or none")

    if missing_data is "drop":
        df = df.dropna()
        print("Nan values dropped.")

    elif missing_data is "impute":
        imputer = SimpleImputer(missing_values=np.nan, strategy="mean")
        df = imputer.fit_transform(df)
        print("Nan values imputed")
    else:
        raise ValueError("Invalid missing_data strategy")

    if outliers_strategy is "drop":
        max_bound = df.quantile(0.95)
        min_bound = df.quantile(0.05)
        df = df[(df > min_bound) & (df < max_bound)].dropna()
        print("Outliers dropped.")
    
    elif outliers_strategy is "stl_dec":
        
        print("Stl Decomposition is not yet ready")
    
    elif outliers_strategy is "rolling":
        print("Rolling curve is not yet ready")
    
    elif outliers_strategy is "hampel":
        print("Hampel filter is not yet ready")
    
