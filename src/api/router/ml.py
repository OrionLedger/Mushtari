from fastapi import APIRouter, HTTPException
from serving.services.predict_product import predict_product
from serving.services.forecast_product import forecast_product
from serving.services.add_records import add_sales_record
from serving.services.train_xgboost_regressor_sales import train_xgboost_regressor

router = APIRouter(prefix="/api", tags=["ML"])


@router.post("/predict")
def predict_api(payload: dict):
    """
    payload example:
    {
        "product_id": 1,
        "features": {
            "lag_1": 10,
            "lag_7": 12,
            "month": 1
        }
    }
    """
    try:
        return predict_product(payload)
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
def add_sales_api(payload: dict):
    """
    payload example:
    {
        "table_name": "Sales",
        "record": {
            "product_id": 1,
            "date": "2026-01-23",
            "sales": 15
        }
    }
    """
    try:
        add_sales_record(
            record=payload["record"],
            table_name=payload.get("table_name", "Sales")
        )
        return {
            "status": "success",
            "message": "Record inserted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.patch("/train/xgboost")
def retrain_xgboost_api(payload: dict):
    try:
        train_xgboost_regressor(
            product_id=payload["product_id"],
            columns=payload.get("columns", ["sales"]),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            test_size=payload.get("test_size", 0.2)
        )

        return {
            "status": "retrained",
            "product_id": payload["product_id"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
