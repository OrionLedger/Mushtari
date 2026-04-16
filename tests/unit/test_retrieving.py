import pytest
from unittest.mock import MagicMock, patch, ANY
from src.retrieving.get_product_sales import get_product_sales

@pytest.fixture
def mock_repo():
    return MagicMock()

def test_get_product_sales_no_dates(mock_repo):
    product_id = 1
    columns = ['sales', 'date']
    get_product_sales(product_id, columns, repo=mock_repo)
    
    mock_repo.get_record.assert_called_once_with(
        table_name='sales', 
        filters={"product_id": product_id}, 
        columns=columns
    )

def test_get_product_sales_with_start_date(mock_repo):
    product_id = 1
    columns = ['sales']
    start_date = '2023-01-01'
    get_product_sales(product_id, columns, start_date=start_date, repo=mock_repo)
    
    mock_repo.get_record.assert_called_once_with(
        table_name='sales', 
        filters={"product_id": product_id, "sell_date__gte": start_date}, 
        columns=columns
    )

def test_get_product_sales_with_end_date(mock_repo):
    product_id = 1
    columns = ['sales']
    end_date = '2023-12-31'
    get_product_sales(product_id, columns, end_date=end_date, repo=mock_repo)
    
    mock_repo.get_record.assert_called_once_with(
        table_name='sales', 
        filters={"product_id": product_id, "sell_date__lte": end_date}, 
        columns=columns
    )

def test_get_product_sales_with_both_dates(mock_repo):
    product_id = 1
    columns = ['sales']
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    get_product_sales(product_id, columns, start_date=start_date, end_date=end_date, repo=mock_repo)
    
    mock_repo.get_record.assert_called_once_with(
        table_name='sales', 
        filters={
            "product_id": product_id, 
            "sell_date__gte": start_date,
            "sell_date__lte": end_date
        }, 
        columns=columns
    )

@patch('src.retrieving.get_product_sales.get_repository')
def test_get_product_sales_default_repo(mock_get_repo):
    # Test that it calls get_repository if repo is None
    product_id = 1
    columns = ['sales']
    get_product_sales(product_id, columns)
    # Use ANY for connection params as they depend on environment/settings
    mock_get_repo.assert_called_once_with(
        "cassandra",
        username=ANY,
        password=ANY,
        contact_points=ANY,
        port=ANY
    )
