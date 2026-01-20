import xgboost as xgb
from os import environ
import joblib

def load_xgboost_model(
        model_name: str,
        models_dir: str = environ.get("MODELS_DIR"),
        device: str = 'cpu'
        ) -> xgb.XGBRegressor:
    """
    Load a pre-trained XGBoost model from the specified file path.
    Args:
        model_name (str): The name of the model file to load.
        models_dir (str): The directory where the model is stored.
        device (str): The device to use for inference ('cpu' or 'cuda').
    """
    model = xgb.XGBRegressor()
    model.load_model(f"{models_dir}{model_name}")
    model.set_params(device=device)
    return model

def load_sklearn_model(
        model_name: str,
        models_dir: str = environ.get("MODELS_DIR")
        ):
    """
    Load a pre-trained scikit-learn model from the specified file path.

    Args:
        model_name (str): The name of the model file to load.
        models_dir (str): The directory where the model is stored.
    """
    model = joblib.load(f"{models_dir}{model_name}")
    return model