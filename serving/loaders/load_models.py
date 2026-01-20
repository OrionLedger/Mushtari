import xgboost as xgb
from os import environ

MODELS_DIR = environ.get("MODELS_DIR") or "./models/"
booster = xgb.Booster()
_models = dict()

def load_model(model_name: str):
    global _models
    if _models[model_name] is None:
        _models[model_name] = booster.load_model(f"{MODELS_DIR}{model_name}.json")

    return _models

def get_model(model_name: str):
    if _models[model_name] is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _models[model_name]