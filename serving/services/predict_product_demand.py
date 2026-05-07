from serving.loaders.load_models import get_model
from src.retrieving.get_product_sales import get_product_sales
from serving.services.inference_logger import log_prediction
import time
import xgboost as xgb

# Predict next value product demand using trained XGBoost model
def predict_product_demand(product_id, 
                           model_name="xgb_model", 
                           columns=None,
                           start_date=None,
                           end_date=None
    ):
    """
    Predicts the demand for a specific product.
    """
    start_time = time.time()
    
    try:
        # 1. Load Model
        model = get_model(model_name)
        
        # 2. Extract Features
        data = get_product_sales(product_id, 
                                columns=columns, 
                                start_date=start_date, 
                                end_date=end_date
            )
        
        if data is None or (hasattr(data, "empty") and data.empty):
            return {"prediction": 0.0, "status": "no_data"}

        # 3. Perform Inference
        predictions = model.predict(data)
        result = float(predictions[0]) if hasattr(predictions, "__getitem__") else float(predictions)
        
        latency = (time.time() - start_time) * 1000
        
        # 4. LOG TELEMETRY (Phase 2 Requirement)
        log_prediction(
            product_id=product_id,
            result=result,
            model_version=model_name,
            latency_ms=latency
        )
        
        return {
            "product_id": product_id,
            "prediction": result,
            "latency_ms": latency,
            "status": "success"
        }
    except Exception as e:
        return {"prediction": 0.0, "status": "error", "message": str(e)}