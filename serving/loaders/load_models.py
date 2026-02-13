import xgboost as xgb
from os import environ

MODELS_DIR = environ.get("MODELS_DIR") or "./models/"
booster = xgb.Booster()
_models = dict()

def load_model(model_name: str):
    """
    Loads a model from the specified path.
    
    Args:
        model_name: The name of the model to load.
    
    Returns:
        The loaded model.
    """
    global _models
    if _models[model_name] is None:
        _models[model_name] = booster.load_model(f"{MODELS_DIR}{model_name}.json")

    return _models

def get_model(model_name: str):
    """
    Retrieves a loaded model.
    
    Args:
        model_name: The name of the model to retrieve.
    
    Returns:
        The loaded model.
    """
    if _models[model_name] is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _models[model_name]