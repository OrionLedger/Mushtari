import pytest
from unittest.mock import MagicMock, patch
from src.retrieving.get_product_sales import get_product_sales

@pytest.fixture
def mock_repo():
    return MagicMock()

def test_get_product_sales_no_dates(mock_repo):
    product_id = 1
    columns = ['sales', 'date']
    get_product_sales(product_id, columns, repo=mock_repo)
    
    mock_repo.get_sales_records.assert_called_once_with(
        'sales', product_id, columns
    )

def test_get_product_sales_with_start_date(mock_repo):
    product_id = 1
    columns = ['sales']
    start_date = '2023-01-01'
    get_product_sales(product_id, columns, start_date=start_date, repo=mock_repo)
    
    mock_repo.get_sales_records.assert_called_once_with(
        'sales', product_id, columns, start_date=start_date
    )

def test_get_product_sales_with_end_date(mock_repo):
    product_id = 1
    columns = ['sales']
    end_date = '2023-12-31'
    get_product_sales(product_id, columns, end_date=end_date, repo=mock_repo)
    
    mock_repo.get_sales_records.assert_called_once_with(
        'sales', product_id, columns, end_date=end_date
    )

def test_get_product_sales_with_both_dates(mock_repo):
    product_id = 1
    columns = ['sales']
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    get_product_sales(product_id, columns, start_date=start_date, end_date=end_date, repo=mock_repo)
    
    mock_repo.get_sales_records.assert_called_once_with(
        'sales', product_id, columns, start_date=start_date, end_date=end_date
    )

@patch('src.retrieving.get_product_sales.CassandraRepository')
def test_get_product_sales_default_repo(mock_repo_class):
    # Test that it instantiates CassandraRepository if repo is None
    product_id = 1
    columns = ['sales']
    get_product_sales(product_id, columns)
    mock_repo_class.assert_called_once()
