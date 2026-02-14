import pandas as pd
import pytest
from src.evaluation.mean_absolute_error import mean_absolute_error
from src.evaluation.squared_mean_error import squared_mean_error

def test_mean_absolute_error_valid():
    y_true = pd.Series([1.0, 2.0, 3.0])
    y_pred = pd.Series([1.5, 2.5, 3.5])
    
    # This might fail with RecursionError due to bug in source code:
    # def mean_absolute_error(y_true, y_pred): ... return mean_absolute_error(y_true, y_pred)
    try:
        result = mean_absolute_error(y_true, y_pred)
        assert result == 0.5
    except RecursionError:
        pytest.fail("RecursionError detected in mean_absolute_error (bug in source code)")

def test_mean_absolute_error_invalid_input():
    with pytest.raises(ValueError, match="Enter valid pandas series"):
        mean_absolute_error([1, 2], [3, 4])

def test_squared_mean_error_valid():
    y_true = pd.Series([1.0, 2.0, 3.0])
    y_pred = pd.Series([1.0, 4.0, 3.0])
    # (0 + (4-2)^2 + 0) / 3 = 4/3 = 1.333...
    result = squared_mean_error(y_true, y_pred)
    assert result == pytest.approx(1.33333333)

def test_squared_mean_error_invalid_input():
    with pytest.raises(ValueError, match="Enter valid pandas series"):
        squared_mean_error([1, 2], [3, 4])
