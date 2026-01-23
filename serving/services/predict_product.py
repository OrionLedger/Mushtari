import pandas as pd
import xgboost as xgb
from os import environ

MODELS_DIR = environ.get("MODELS_DIR", "./models/")

def predict_product(payload: dict):
    product_id = payload["product_id"]
    features = payload["features"]

    model_path = f"{MODELS_DIR}xgboost_regressor_product_{product_id}.json"

    model = xgb.Booster()
    model.load_model(model_path)

    X = pd.DataFrame([features])
    dmatrix = xgb.DMatrix(X)

    prediction = float(model.predict(dmatrix)[0])

    return {
        "product_id": product_id,
        "prediction": prediction
    }
