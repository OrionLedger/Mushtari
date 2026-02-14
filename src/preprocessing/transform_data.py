from sklearn.preprocessing import PowerTransformer
import pandas as pd
import numpy as np
from typing import Literal

def log_transformer(
    df: pd.DataFrame,
    method:Literal["box-cox", "yeo-johnson"] = 'box-cox'
):
    """
    Applies a log transformation to the dataframe.
    
    Args:
        df: The dataframe to apply the log transformation to.
        method: The method to use for the log transformation.
    
    Returns:
        The dataframe with the log transformation applied.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Enter a valid dataframe")
    
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        raise ValueError("Dataframe does not contain numeric columns")

    # Cast to float to avoid precision/dtype issues during insertion
    df = df.astype({col: float for col in numeric_df.columns})
    numeric_df = df.select_dtypes(include=[np.number])

    transformer = PowerTransformer(method)
    transformed_numeric_df = transformer.fit_transform(numeric_df)

    df.loc[:, numeric_df.columns] = transformed_numeric_df
    return df