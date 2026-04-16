import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    """Test the /health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_prometheus_metrics_endpoint():
    """Test the /metrics endpoint existence"""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus metrics are usually plain text
    assert "# HELP" in response.text

@patch('api.router.demand.predict_product_demand')
def test_batch_predict_success(mock_predict):
    """Test batch prediction endpoint success"""
    mock_predict.return_value = {"prediction": 50.0}
    response = client.post("/api/predict/batch", json={
        "product_ids": [1, 2, 3]
    })
    assert response.status_code == 200
    results = response.json()
    assert "predictions" in results
    assert len(results["predictions"]) == 3
    assert results["predictions"]["1"]["prediction"] == 50.0

@patch('api.router.data.etl_pipeline_flow')
def test_etl_extract_trigger(mock_etl):
    """Test the ETL extraction trigger (Background Task)"""
    response = client.post("/api/data/extract", json={
        "source_type": "csv",
        "source_config": {"file_path": "test.csv"}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    # Note: background tasks are usually executed after the response is returned in a real app,
    # but in TestClient they are gathered. However, we are testing the endpoint logic.

def test_market_fit_kpi_calculation():
    """Test the Market Fit KPI calculation endpoint"""
    response = client.post("/api/kpi/market-fit", json={
        "actuals": [10.0, 20.0, 30.0],
        "predictions": [11.0, 19.0, 31.0]
    })
    assert response.status_code == 200
    data = response.json()
    assert "forecast_bias" in data
    assert "inventory_efficiency_score" in data
