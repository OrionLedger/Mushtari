import xgboost as xgb
from os import environ
import joblib

MODELS_DIR = environ.get("MODELS_DIR") or "./models/"
MODEL_NAME = "xgb_model.pkl"
_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load(f"{MODELS_DIR}{MODEL_NAME}")

    return _model

def get_model():
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _model
