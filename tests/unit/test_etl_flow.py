import pytest
import pandas as pd
from unittest.mock import patch
from etl.flows.etl_flow import dispatch_extract

@patch('etl.flows.etl_flow.extract_from_csv')
def test_dispatch_extract_csv(mock_extract_csv):
    """Test dispatching to the CSV extractor."""
    mock_df = pd.DataFrame({'a': [1, 2]})
    mock_meta = {'source_name': 'test.csv'}
    mock_extract_csv.fn.return_value = (mock_df, mock_meta)
    
    # We call .fn because it's a Prefect task
    df, meta = dispatch_extract.fn(source_type="csv", source_config={"file_path": "test.csv"})
    
    assert len(df) == 2
    assert meta['source_name'] == 'test.csv'
    mock_extract_csv.fn.assert_called_once_with(file_path="test.csv")

def test_dispatch_extract_invalid():
    """Test dispatching with an invalid source type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown source_type"):
        dispatch_extract.fn(source_type="invalid_type", source_config={})
