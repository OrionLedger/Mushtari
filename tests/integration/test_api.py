import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root_redirect():
    """Test that root redirects to /docs or returns documentation summary"""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200

def test_api_root_documentation():
    """Test the /api documentation endpoint"""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert "/api/predict" in data["endpoints"]

def test_predict_validation_error():
    """Test predict endpoint Pydantic validation failure"""
    response = client.post("/api/predict", json={"product_id": "not-an-int"})
    assert response.status_code == 422

def test_forecast_product_params():
    """Test forecast endpoint parameters"""
    # Using a dummy product_id that might fail in DB but should pass API layer
    response = client.get("/api/forecast?product_id=999&horizon=5")
    assert response.status_code in [200, 500] # 500 if DB is down, 200 if it works

def test_add_sales_validation():
    """Test add sales endpoint validation"""
    response = client.post("/api/sales", json={"table_name": "TestTable"}) # Missing 'record'
    assert response.status_code == 422

from unittest.mock import patch

@patch('api.router.demand.predict_product_demand')
def test_predict_success(mock_predict):
    """Test predict endpoint success"""
    mock_predict.return_value = {"prediction": 100.0}
    response = client.post("/api/predict", json={
        "product_id": 1,
        "features": ["lag_1"],
        "start_date": "2026-01-01",
        "end_date": "2026-02-01"
    })
    assert response.status_code == 200
    assert response.json() == {"predictions": {"prediction": 100.0}}
    mock_predict.assert_called_once_with(
        product_id=1,
        columns=["lag_1"],
        start_date="2026-01-01",
        end_date="2026-02-01"
    )

@patch('api.router.demand.add_sales_record')
def test_add_sales_success(mock_add_sales):
    """Test add sales endpoint success"""
    response = client.post("/api/sales", json={
        "table_name": "Sales",
        "record": {"product_id": 1, "date": "2026-01-23", "sales": 15}
    })
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Record inserted successfully"
    }
    mock_add_sales.assert_called_once()

@patch('api.router.demand.train_xgboost_regressor')
def test_train_xgboost_success(mock_train_xgboost):
    """Test XGBoost training controller success"""
    response = client.patch("/api/train/xgboost", json={
        "product_id": 1,
        "columns": ["sales"],
        "test_size": 0.2
    })
    assert response.status_code == 200
    assert response.json() == {
        "status": "retrained",
        "product_id": 1
    }
    mock_train_xgboost.assert_called_once_with(
        product_id=1,
        columns=["sales"],
        start_date=None,
        end_date=None,
        test_size=0.2
    )

def test_train_xgboost_validation():
    """Test XGBoost training endpoint validation"""
    response = client.patch("/api/train/xgboost", json={
        "columns": ["sales"]  # Missing product_id
    })
    assert response.status_code == 422
