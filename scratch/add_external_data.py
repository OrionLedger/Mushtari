import sys
from pathlib import Path
from repo import get_repository
from etl.config.settings import get_settings

def add_data():
    settings = get_settings().extract.postgres
    # Override dbname to point to external_source_db
    source_settings = {
        "user": settings.user,
        "password": settings.password,
        "host": settings.host,
        "port": settings.port,
        "dbname": "external_source_db"
    }
    
    try:
        repo = get_repository("postgres", shared=False, **source_settings)
        repo.connect()
        
        new_data = [
            {"product_id": 500, "quantity": 10.5, "price_at_sale": 99.99, "source_identifier": "MANUAL_BATCH_01"},
            {"product_id": 501, "quantity": 5.0, "price_at_sale": 45.50, "source_identifier": "MANUAL_BATCH_01"},
            {"product_id": 502, "quantity": 2.2, "price_at_sale": 1200.00, "source_identifier": "MANUAL_BATCH_01"},
            {"product_id": 1, "quantity": 100.0, "price_at_sale": 10.00, "source_identifier": "MANUAL_BATCH_01"},
        ]
        
        print(f"Adding {len(new_data)} records to legacy_sales in external_source_db...")
        result = repo.bulk_insert("legacy_sales", new_data)
        print(f"Success: {result}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_data()
