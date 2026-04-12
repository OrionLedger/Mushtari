import pytest
from unittest.mock import patch, MagicMock
from etl.load.mlflow_loader import log_to_mlflow
from etl.schema.models import DatasetSchema
import pandas as pd

@patch("etl.load.mlflow_loader.mlflow", create=True)
@patch("etl.load.mlflow_loader.get_settings")
def test_log_to_mlflow_success(mock_get_settings, mock_mlflow):
    """Test logging to MLflow successful path."""
    # Setup mocks
    mock_settings = MagicMock()
    mock_settings.load.mlflow_tracking = True
    mock_settings.load.mlflow_experiment_name = "test_experiment"
    mock_get_settings.return_value = mock_settings
    
    mock_run = MagicMock()
    mock_run.info.run_id = "test_run_123"
    mock_mlflow.start_run.return_value.__enter__.return_value = mock_run

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

    with patch("etl.load.mlflow_loader.Path") as mock_path:
        mock_path_instance = mock_path.return_value
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        
        # We need to test the logic of log_to_mlflow.
        # Since it's a Prefect task, we call .fn to execute the actual Python function
        run_id = log_to_mlflow.fn(
            data_path="/fake/path/data.parquet",
            schema=mock_schema,
            run_name="test_run",
            extra_params={"param": "value"}
        )

        assert run_id == "test_run_123"
        mock_mlflow.set_experiment.assert_called_once_with("test_experiment")
        mock_mlflow.log_param.assert_any_call("source_name", "test_source")
        mock_mlflow.log_param.assert_any_call("param", "value")

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
