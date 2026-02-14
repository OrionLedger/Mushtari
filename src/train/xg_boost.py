import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt
import mlflow
import mlflow.xgboost

def train_xg_boost_regressor(X_train, y_train, X_eval, y_eval, X_test, y_test,
                            estimators=100, 
                            max_depth=5, 
                            learning_rate=0.1
                            ):
    """
    Trains an XGBoost regressor model and logs parameters, metrics, and the model to MLflow.
    
    Args:
        X_train: The training data features.
        y_train: The training data target.
        X_eval: The evaluation data features.
        y_eval: The evaluation data target.
        X_test: The test data features.
        y_test: The test data target.
        estimators: The number of estimators.
        max_depth: The maximum depth of the tree.
        learning_rate: The learning rate.
    
    Returns:
        The trained XGBoost regressor model.
    """
    
    with mlflow.start_run():
        # Log parameters
        mlflow.log_params({
            "estimators": estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "objective": 'reg:absoluteerror'
        })

        model = xgb.XGBRegressor(
            objective='reg:absoluteerror',
            n_estimators=estimators,
            max_depth=max_depth,
            learning_rate=learning_rate
        )

        model.fit(X_train, y_train, eval_set=[(X_eval, y_eval)], verbose=False)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("mae", mae)
        
        # Log model
        mlflow.xgboost.log_model(model, artifact_path="model")
        
        print(f"Mean Absolute Error XGBoost Regressor: {mae:.4f}")

    return model