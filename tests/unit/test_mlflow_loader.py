import pytest
from unittest.mock import patch, MagicMock
from etl.load.mlflow_loader import log_to_mlflow
from etl.schema.models import DatasetSchema
import pandas as pd
from pathlib import Path
import sys

@pytest.fixture
def mock_mlflow():
    with patch("mlflow.start_run") as mock_start_run, \
         patch("mlflow.set_experiment") as mock_set_ext, \
         patch("mlflow.log_param") as mock_log_param, \
         patch("mlflow.log_metric") as mock_log_metric, \
         patch("mlflow.log_artifact") as mock_log_art:
        
        mock_mlflow_obj = MagicMock()
        mock_mlflow_obj.start_run = mock_start_run
        mock_mlflow_obj.set_experiment = mock_set_ext
        mock_mlflow_obj.log_param = mock_log_param
        mock_mlflow_obj.log_metric = mock_log_metric
        mock_mlflow_obj.log_artifact = mock_log_art
        
        mock_run = MagicMock()
        mock_run.info.run_id = "test_run_123"
        mock_start_run.return_value.__enter__.return_value = mock_run
        
        # Patch sys.modules to ensure the local import inside the function gets the mock
        with patch.dict('sys.modules', {'mlflow': mock_mlflow_obj}):
            yield mock_mlflow_obj

@patch("etl.load.mlflow_loader.get_settings")
def test_log_to_mlflow_success(mock_get_settings, mock_mlflow, tmp_path):
    """Test logging to MLflow successful path."""
    # Setup mocks
    mock_settings = MagicMock()
    mock_settings.load.mlflow_tracking = True
    mock_settings.load.mlflow_experiment_name = "test_experiment"
    mock_get_settings.return_value = mock_settings
    
    mock_schema = MagicMock(spec=DatasetSchema)
    mock_schema.source_name = "test_source"
    mock_schema.source_type = "csv"
    mock_schema.field_count = 5
    mock_schema.version = "1.0"
    mock_schema.record_count = 100
    mock_schema.issues = []
    mock_schema.nullable_fields.return_value = []
    mock_schema.nested_fields.return_value = []
    mock_schema.model_dump_json.return_value = "{}"

    # Create a real dummy data file in tmp_path
    data_file = tmp_path / "data.parquet"
    data_file.write_text("dummy data")
    
    # Execute the Prefect task
    run_id = log_to_mlflow.fn(
        data_path=str(data_file),
        schema=mock_schema,
        run_name="test_run",
        extra_params={"param": "value"}
    )

    assert run_id == "test_run_123"
    mock_mlflow.set_experiment.assert_called_once_with("test_experiment")
    mock_mlflow.log_param.assert_any_call("source_name", "test_source")
    mock_mlflow.log_param.assert_any_call("param", "value")
    # Verify that log_artifact was called for both schema and dataset
    assert mock_mlflow.log_artifact.call_count == 2

@patch("etl.load.mlflow_loader.get_settings")
def test_log_to_mlflow_disabled(mock_get_settings):
    """Test log_to_mlflow when tracking is disabled."""
    mock_settings = MagicMock()
    mock_settings.load.mlflow_tracking = False
    mock_get_settings.return_value = mock_settings

    mock_schema = MagicMock(spec=DatasetSchema)
    
    run_id = log_to_mlflow.fn(
        data_path="/fake/path/data.parquet",
        schema=mock_schema
    )
    
    assert run_id is None
