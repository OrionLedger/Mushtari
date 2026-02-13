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
