import pandas as pd
import numpy as np
import pytest
from src.preprocessing.clean_data import clean_data
from src.preprocessing.normalize_data import normalize_data
from src.preprocessing.transform_data import log_transformer

def test_clean_data_drop_nan():
    df = pd.DataFrame({'a': [1, 2, np.nan], 'b': [4, 5, 6]})
    cleaned_df = clean_data(df, outliers_strategy="stl_dec", missing_data="drop")
    assert len(cleaned_df) == 2
    assert cleaned_df.isna().sum().sum() == 0

def test_clean_data_impute_nan():
    df = pd.DataFrame({'a': [1, 2, np.nan], 'b': [4, 5, 6]})
    # Now returns a DataFrame
    cleaned_df = clean_data(df, outliers_strategy="stl_dec", missing_data="impute")
    assert isinstance(cleaned_df, pd.DataFrame)
    assert cleaned_df.isna().sum().sum() == 0

def test_clean_data_invalid_missing_strategy():
    df = pd.DataFrame({'a': [1, 2], 'b': [4, 5]})
    with pytest.raises(ValueError, match="missing_data must be impute, drop, or none"):
        clean_data(df, outliers_strategy="drop", missing_data="invalid")

def test_clean_data_drop_outliers():
    # Create a distribution where some values are clearly outside 5th-95th percentile
    data = {'a': list(range(100))} # 0 to 99
    df = pd.DataFrame(data)
    # Quantiles: 0.05 is 4.95, 0.95 is 94.05
    cleaned_df = clean_data(df, outliers_strategy="drop", missing_data="none")
    # Should drop values < 5 and > 94 (approx)
    assert cleaned_df['a'].min() > 0
    assert cleaned_df['a'].max() < 99
    assert len(cleaned_df) < 100

def test_normalize_data_standard():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    normalized = normalize_data(df, strategy="standard")
    assert isinstance(normalized, pd.DataFrame)
    # Standard scaler should result in mean close to 0 and std close to 1
    assert np.allclose(normalized.mean(axis=0), 0, atol=1e-7)

def test_normalize_data_minmax():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    normalized = normalize_data(df, strategy="minmax")
    assert normalized.min().min() == 0
    assert normalized.max().max() == 1

def test_normalize_data_invalid_strategy():
    df = pd.DataFrame({'a': [1, 2, 3]})
    with pytest.raises(ValueError, match="strategy must be standard, minmax, robust, or none"):
        normalize_data(df, strategy="invalid")

def test_log_transformer_box_cox():
    # Box-cox requires strictly positive data
    df = pd.DataFrame({'a': [1, 2, 3, 4, 5], 'b': [10, 20, 30, 40, 50]})
    transformed_df = log_transformer(df, method="box-cox")
    assert isinstance(transformed_df, pd.DataFrame)
    assert not transformed_df.equals(df)

def test_log_transformer_non_numeric():
    df = pd.DataFrame({'a': ['x', 'y', 'z']})
    with pytest.raises(ValueError, match="Dataframe does not contain numeric columns"):
        log_transformer(df)

def test_log_transformer_invalid_input():
    with pytest.raises(ValueError, match="Enter a valid dataframe"):
        log_transformer([1, 2, 3])
