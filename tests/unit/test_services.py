import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from serving.services.forecast_product import forecast_product
from serving.services.add_records import add_sales_record
from serving.services.predict_product_demand import predict_product_demand

@pytest.fixture
def mock_repo():
    """Fixture for a mocked CassandraRepository."""
    return MagicMock()

@pytest.fixture
def sample_sales_data():
    """Dummy sales data returned by the repo."""
    return [
        {"sales": 10.0, "sell_date": "2026-01-01"},
        {"sales": 12.0, "sell_date": "2026-01-02"},
        {"sales": 15.0, "sell_date": "2026-01-03"}
    ]

def test_add_sales_record_calls_repo(mock_repo):
    """Verify that add_sales_record correctly delegates to the repository."""
    test_record = {"product_id": 1, "sales": 10}
    add_sales_record(record=test_record, table_name="TestTable", repo=mock_repo)
    
    # Assert that the repo's add method was called with correct args
    mock_repo.add_sales_record.assert_called_once_with(
        table_name="TestTable",
        record=test_record
    )

@patch("serving.services.forecast_product.start_arima_forecaster")
def test_forecast_product_orchestration(mock_arima, mock_repo, sample_sales_data):
    """Verify that forecast_product fetches data and calls the ARIMA forecaster."""
    # Setup mocks
    mock_repo.get_sales_records.return_value = sample_sales_data
    mock_model = MagicMock()
    # Mock return: model, y_pred, conf_int
    mock_arima.return_value = (mock_model, np.array([16.0, 17.0]), np.array([[15, 17], [16, 18]]))
    
    # Execute
    result = forecast_product(product_id=1, horizon=2, repo=mock_repo)
    
    # Assertions
    assert result["product_id"] == 1
    assert result["forecast"] == [16.0, 17.0]
    # Verify the model was called with the float list extracted from sample_sales_data
    mock_arima.assert_called_once()
    actual_y = mock_arima.call_args.kwargs["y"]
    assert actual_y == [10.0, 12.0, 15.0]

@patch("serving.services.predict_product_demand.get_model")
@patch("serving.services.predict_product_demand.get_product_sales")
def test_predict_product_demand_orchestration(mock_get_sales, mock_get_model):
    """Verify that predict_product_demand connects model and retrieval layers."""
    # Setup
    mock_model = MagicMock()
    mock_get_model.return_value = mock_model
    mock_model.predict.return_value = np.array([20.5])
    mock_get_sales.return_value = [{"sales": 10}]
    
    # Execute
    prediction = predict_product_demand(product_id=1)
    
    # Assert
    assert prediction == [20.5]
    mock_get_model.assert_called_with("xgb_model")
    mock_model.predict.assert_called_once()
