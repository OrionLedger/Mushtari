from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
import time
import asyncio
from typing import Optional

from serving.services.predict_product_demand import predict_product_demand
from serving.services.llm_forecast import llm_forecast_product
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
        from repo.current import get_active_repository
        repo = get_active_repository()
        rows = await run_in_threadpool(
            repo.get_record,
            table_name="products",
            columns=["id", "name"]
        )
        return [{"id": str(row["id"]), "name": row["name"]} for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching products: {str(e)}")


@router.get("/products/{product_id}")
async def get_product_api(product_id: int):
    """
    Get product details from the database.
    """
    try:
        from repo.current import get_active_repository
        repo = get_active_repository()
        rows = await run_in_threadpool(
            repo.get_record,
            table_name="products",
            filters={"id": product_id},
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        return rows[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/sales")
async def get_product_sales_api(
    product_id: int,
    scope: str = "month",
    start_date: Optional[str] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
):
    """
    Get sales history for a product, aggregated by the given scope.
    """
    try:
        from repo.current import get_active_repository
        repo = get_active_repository()
        rows = await run_in_threadpool(
            repo.get_record,
            table_name="sales",
            filters={"product_id": product_id},
            columns=["ds", "quantity", "price_at_sale"],
        )
        if not rows:
            return {"sales": []}

        import pandas as pd
        df = pd.DataFrame(rows)
        df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)
        df["quantity"] = df["quantity"].apply(float)

        if start_date:
            df = df[df["ds"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["ds"] <= pd.to_datetime(end_date)]

        if df.empty:
            return {"sales": []}

        freq_map = {"day": "D", "week": "W", "month": "ME", "year": "QE", "5years": "YE", "beginning": "W"}
        freq = freq_map.get(scope, "ME")

        resampled = df.resample(freq, on="ds")["quantity"].sum().reset_index()
        sales = []
        for _, r in resampled.iterrows():
            sales.append({
                "date": r["ds"].strftime("%Y-%m-%d"),
                "quantity": int(r["quantity"]),
            })
        return {"sales": sales}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def llm_forecast_api(product_id: int, horizon: int = 7, scope: str = "day"):
    """
    example:
    /api/forecast?product_id=1&horizon=7&scope=month

    Uses LLM (Groq/Llama) to generate the forecast, with ARIMA fallback.
    """
    valid_scopes = {"day", "week", "month", "year", "5years", "beginning"}
    if scope not in valid_scopes:
        raise HTTPException(status_code=400, detail=f"Invalid scope '{scope}'. Use: {', '.join(sorted(valid_scopes))}")
    try:
        cache_key = f"llm_{product_id}_{horizon}_{scope}"
        current_time = time.time()
        
        # Evaluate Cache Hit
        if cache_key in _forecast_cache:
            cached_data, timestamp = _forecast_cache[cache_key]
            if current_time - timestamp < CACHE_TTL:
                return cached_data
                
        # Cache Miss - Offload LLM call to threadpool
        forecast_result = await run_in_threadpool(
            llm_forecast_product,
            product_id=product_id,
            horizon=horizon,
            scope=scope
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
