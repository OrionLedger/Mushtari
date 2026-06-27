from src.retrieving.get_product_sales import get_product_sales
from models.forecasting.arima import start_arima_forecaster
from serving.services.inference_logger import log_prediction
import time

def forecast_product(product_id: int, horizon: int, repo = None):
    start_time = time.time()
    
    data = get_product_sales(
        product_id=product_id,
        columns=["quantity"],
        repo=repo
    )

    if not data:
        return {"product_id": product_id, "forecast": [], "status": "no_data"}

    y = [float(r["quantity"]) for r in data]

    model, y_pred, conf_int = start_arima_forecaster(
        y=y,
        n_periods=horizon
    )

    result_list = y_pred.tolist()
    latency = (time.time() - start_time) * 1000

    # Log the first prediction point as the primary inference metric
    log_prediction(
        product_id=product_id,
        result=float(result_list[0]) if result_list else 0.0,
        model_version="arima_v1",
        latency_ms=latency
    )

    return {
        "product_id": product_id,
        "horizon": horizon,
        "forecast": result_list,
        "latency_ms": latency,
        "status": "success"
    }
