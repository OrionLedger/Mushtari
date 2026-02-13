from fastapi import APIRouter, HTTPException
from serving.services.predict_product_demand import predict_product_demand
from serving.services.forecast_product import forecast_product
from serving.services.add_records import add_sales_record
from serving.services.train_xgboost_regressor_sales import train_xgboost_regressor
from api.models.demand_models import PredictPayload, SalesPayload, TrainPayload

router = APIRouter(prefix="/api", tags=["ML"])


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
            "/api/forecast": "GET - Forecast demand for a given product ID and horizon.",
            "/api/sales": "POST - Add a new sales record to the database.",
            "/api/train/xgboost": "PATCH - Trigger retraining of the XGBoost model for a product."
        },
        "swagger_docs": "/docs"
    }


@router.post("/predict")
def predict_api(payload: PredictPayload):
    """
    Predict product demand based on historical features.
    """
    try:
        return predict_product_demand(
            product_id=payload.product_id,
            columns=payload.features,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
def forecast_api(
    product_id: int,
    horizon: int = 7
):
    """
    example:
    /api/forecast?product_id=1&horizon=7
    """
    try:
        return forecast_product(
            product_id=product_id,
            horizon=horizon
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sales")
def add_sales_api(payload: SalesPayload):
    """
    Add a new sales record to the database.
    """
    try:
        add_sales_record(
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
def retrain_xgboost_api(payload: TrainPayload):
    """
    Trigger retraining of the XGBoost model for a specific product.
    """
    try:
        train_xgboost_regressor(
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
