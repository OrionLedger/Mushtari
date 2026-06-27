from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
import time
import asyncio

from serving.services.predict_product_demand import predict_product_demand
from serving.services.forecast_product import forecast_product
from serving.services.llm_insight import llm_product_insight
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
            "/api/products": "GET - List all unique product IDs available in the database.",
            "/api/predict": "POST - Predict product demand based on historical features.",
            "/api/predict/batch": "POST - Predict demand for multiple products concurrently.",
            "/api/forecast": "GET - Forecast demand for a given product ID and horizon. (Cached)",
            "/api/sales": "POST - Add a new sales record to the database.",
            "/api/train/xgboost": "PATCH - Trigger retraining of the XGBoost model for a product."
        },
        "swagger_docs": "/docs"
    }

@router.get("/products")
async def list_products_api():
    """
    List unique product IDs from the sales table.
    """
    try:
        from repo import get_repository
        from etl.config.settings import get_settings
        settings = get_settings().extract.cassandra
        repo = get_repository(
            "cassandra",
            username=settings.username,
            password=settings.password,
            contact_points=settings.contact_points,
            port=settings.port,
            keyspace=settings.keyspace
        )
        
        # In a real app we'd query a Products table, here we'll scan unique product_id from sales
        # Warning: Direct scan of partition keys in Cassandra can be slow on large tables
        # But for this MVP/dashboard, we'll use it.
        # Ideally, we'd have a 'products' table.
        rows = await run_in_threadpool(
            repo.get_record,
            table_name=settings.default_table,
            columns=["product_id"]
        )
        
        # Deduplicate
        pids = sorted(list(set(row["product_id"] for row in rows)))
        return [{"id": str(pid), "name": f"Product {pid}"} for pid in pids]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching products: {str(e)}")


VALID_SCOPES = {"day", "week", "month", "year", "5years", "beginning"}

@router.get("/products/{product_id}/insight")
async def product_insight_api(product_id: int, scope: str = "week", horizon: int = 4):
    """
    Generate import/ordering insights for a product using an LLM.

    Combines product details, sales velocity, forecast, XGBoost prediction,
    and inventory level to produce an actionable reorder recommendation.

    Scope: day, week, month (controls the forecast aggregation for context).
    Horizon: number of forecast periods to include (default 4).
    """
    if scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope '{scope}'. Must be one of: {', '.join(sorted(VALID_SCOPES))}"
        )
    try:
        result = await run_in_threadpool(
            llm_product_insight,
            product_id=product_id,
            scope=scope,
            horizon=horizon,
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message", "Unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
