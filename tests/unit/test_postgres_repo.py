import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import text
from repo.postgres_repo import PostgresRepository

@pytest.fixture
def mock_engine():
    with patch("repo.postgres_repo.create_engine") as mock_create:
        engine = MagicMock()
        mock_create.return_value = engine
        yield engine

def test_postgres_connect(mock_engine):
    repo = PostgresRepository(user="test", password="test", host="localhost", dbname="testdb")
    repo.connect()
    
    assert repo.is_connected() is True
    # Verify selecting 1 was called to test connection
    mock_engine.connect.return_value.__enter__.return_value.execute.assert_called()

def test_postgres_get_record(mock_engine):
    repo = PostgresRepository(connection_uri="postgresql://user:pass@host/db")
    repo.connect()
    
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    # Mock result mapping for a row
    mock_row = MagicMock()
    mock_row._mapping = {"id": 1, "name": "Test"}
    mock_result.__iter__.return_value = [mock_row]
    mock_conn.execute.return_value = mock_result
    
    records = repo.get_record("my_table", filters={"id": 1})
    
    assert len(records) == 1
    assert records[0]["name"] == "Test"
    # Verify SQL generation
    called_sql = mock_conn.execute.call_args[0][0].text
    assert "SELECT * FROM my_table WHERE id = :id" in called_sql

def test_postgres_bulk_insert(mock_engine):
    repo = PostgresRepository(connection_uri="postgresql://user:pass@host/db")
    repo.connect()
    
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    records = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
    
    summary = repo.bulk_insert("my_table", records, batch_size=1)
    
    assert summary["inserted"] == 2
    assert mock_conn.execute.call_count > 0

def test_postgres_delete_record(mock_engine):
    repo = PostgresRepository(connection_uri="postgresql://user:pass@host/db")
    repo.connect()
    
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_conn.execute.return_value.rowcount = 1
    
    success = repo.delete_record("my_table", 123)
    
    assert success is True
    called_sql = mock_conn.execute.call_args[0][0].text
    assert "DELETE FROM my_table WHERE id = :record_id" in called_sql
