from src.retrieving.get_product_sales import get_product_sales
from models.forecasting.arima import start_arima_forecaster
from serving.services.inference_logger import log_prediction
from datetime import datetime, timezone
from collections import defaultdict
import time


SCOPE_AGG_KEYS = {
    "day":    lambda dt: dt.date().isoformat(),
    "week":   lambda dt: f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}",
    "month":  lambda dt: f"{dt.year}-{dt.month:02d}",
    "year":   lambda dt: str(dt.year),
}


def _aggregate_by_scope(data: list, scope: str) -> list:
    """
    Group raw sales records by the requested time granularity.
    Returns a list of summed quantities sorted chronologically.
    """
    key_fn = SCOPE_AGG_KEYS.get(scope)
    if not key_fn:
        scope = "day"
        key_fn = SCOPE_AGG_KEYS[scope]

    buckets = defaultdict(float)
    for row in data:
        dt = row["ds"]
        # Ensure dt is a datetime (it may be a string or datetime)
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        key = key_fn(dt)
        buckets[key] += float(row["quantity"])

    # Sort by key (chronological for ISO formats)
    sorted_keys = sorted(buckets.keys())
    return [buckets[k] for k in sorted_keys]


def forecast_product(product_id: int, horizon: int, scope: str = "day", repo=None):
    start_time = time.time()

    data = get_product_sales(
        product_id=product_id,
        columns=["ds", "quantity"],
        repo=repo
    )

    if not data:
        return {"product_id": product_id, "horizon": horizon, "scope": scope, "forecast": [], "status": "no_data"}

    y = _aggregate_by_scope(data, scope)

    if len(y) < 3:
        return {
            "product_id": product_id,
            "horizon": horizon,
            "scope": scope,
            "forecast": [],
            "status": "no_data",
            "message": f"Not enough {scope}-level data points (got {len(y)}, need at least 3)."
        }

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
        "scope": scope,
        "forecast": result_list,
        "data_points": len(y),
        "latency_ms": latency,
        "status": "success"
    }
