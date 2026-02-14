import pandas as pd
import numpy as np
import pytest
from src.train.xg_boost import train_xg_boost_regressor
import xgboost as xgb

def test_train_xg_boost_regressor():
    # Create small dummy data
    X_train = pd.DataFrame({'feat1': [1, 2, 3, 4, 5], 'feat2': [5, 4, 3, 2, 1]})
    y_train = pd.Series([10, 20, 30, 40, 50])
    
    X_eval = pd.DataFrame({'feat1': [6], 'feat2': [0]})
    y_eval = pd.Series([60])
    
    X_test = pd.DataFrame({'feat1': [7], 'feat2': [-1]})
    y_test = pd.Series([70])
    
    model = train_xg_boost_regressor(
        X_train, y_train, 
        X_eval, y_eval, 
        X_test, y_test,
        estimators=10,
        max_depth=2
    )
    
    assert isinstance(model, xgb.XGBRegressor)
    # Check if we can predict
    preds = model.predict(X_test)
    assert len(preds) == 1
