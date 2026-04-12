from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
import time
import asyncio

from serving.services.predict_product_demand import predict_product_demand
from serving.services.forecast_product import forecast_product
from serving.services.add_records import add_sales_record
from serving.services.train_xgboost_regressor_sales import train_xgboost_regressor
from api.models.demand_models import PredictPayload, PredictBatchPayload, SalesPayload, TrainPayload

router = APIRouter(prefix="/api", tags=["ML"])

_forecast_cache = {}
CACHE_TTL = 3600  # 1 hour TTL for forecast

@router.get("/")
def document_root():
    """
    Returns a summary of the available endpoints in the Demand Analysis API.
    """
    return {
        "message": "Welcome to the Demand Analysis API",
        "description": "This API provides endpoints for demand prediction, forecasting, and data management.",
        "endpoints": {
            "/api/predict": "POST - Predict product demand based on historical features.",
            "/api/predict/batch": "POST - Predict demand for multiple products concurrently.",
            "/api/forecast": "GET - Forecast demand for a given product ID and horizon. (Cached)",
            "/api/sales": "POST - Add a new sales record to the database.",
            "/api/train/xgboost": "PATCH - Trigger retraining of the XGBoost model for a product."
        },
        "swagger_docs": "/docs"
    }

@router.post("/predict")
async def predict_api(payload: PredictPayload):
    """
    Predict product demand based on historical features.
    """
    try:
        predictions = await run_in_threadpool(
            predict_product_demand,
            product_id=payload.product_id,
            columns=payload.features,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
        preds_list = predictions.tolist() if hasattr(predictions, "tolist") else predictions
        return {"predictions": preds_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/batch")
async def predict_batch_api(payload: PredictBatchPayload):
    """
    Predict product demand for multiple products utilizing threadpool concurrency.
    """
    try:
        async def fetch_predict(pid):
            preds = await run_in_threadpool(
                predict_product_demand,
                product_id=pid,
                columns=payload.features,
                start_date=payload.start_date,
                end_date=payload.end_date
            )
            return pid, (preds.tolist() if hasattr(preds, "tolist") else preds)
        
        # Dispatch DB fetching and prediction to threads to avoid blocking asyncio loop
        results = await asyncio.gather(*(fetch_predict(pid) for pid in payload.product_ids))
        
        return {"predictions": {pid: preds for pid, preds in results}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
async def forecast_api(product_id: int, horizon: int = 7):
    """
    example:
    /api/forecast?product_id=1&horizon=7
    """
    try:
        cache_key = f"{product_id}_{horizon}"
        current_time = time.time()
        
        # Evaluate Cache Hit
        if cache_key in _forecast_cache:
            cached_data, timestamp = _forecast_cache[cache_key]
            if current_time - timestamp < CACHE_TTL:
                return cached_data
                
        # Cache Miss - Offload computationally heavy ARIMA auto_core to threadpool
        forecast_result = await run_in_threadpool(
            forecast_product,
            product_id=product_id,
            horizon=horizon
        )
        
        _forecast_cache[cache_key] = (forecast_result, current_time)
        return forecast_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales")
async def add_sales_api(payload: SalesPayload):
    """
    Add a new sales record to the database.
    """
    try:
        await run_in_threadpool(
            add_sales_record,
            record=payload.record,
            table_name=payload.table_name
        )
        return {
            "status": "success",
            "message": "Record inserted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/train/xgboost")
async def retrain_xgboost_api(payload: TrainPayload):
    """
    Trigger retraining of the XGBoost model for a specific product.
    """
    try:
        await run_in_threadpool(
            train_xgboost_regressor,
            product_id=payload.product_id,
            columns=payload.columns,
            start_date=payload.start_date,
            end_date=payload.end_date,
            test_size=payload.test_size
        )

        return {
            "status": "retrained",
            "product_id": payload.product_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
