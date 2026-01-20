from sklearn.preprocessing import PowerTransformer
import pandas as pd
import numpy as np
from typing import Literal

def log_transformer(
    df: pd.DataFrame,
    method:Literal["box-cox", "yeo-johnson"] = 'box-cox'
):
    if type(df) is not pd.DataFrame:
        raise ValueError("Enter a valid dataframe")
    
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        raise ValueError("Dataframe does not contain numeric columns")
    transformer = PowerTransformer(method)
    transformed_numeric_df = transformer.fit_transform(numeric_df)

    df.loc[:, numeric_df.columns] = transformed_numeric_df
    return df