"""
scripts/database/trigger_anomaly_alerts.py

Automation script for Phase 3. Inserts a simulated anomalous sales event
into Cassandra and triggers the AlertEngine to detect and log it.
"""

import sys
from pathlib import Path
import uuid
import time

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from serving.services.alert_engine import AlertEngine
from repo import get_repository
from etl.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger("AnomalyTest")

def execute():
    logger.info("Initializing Anomaly Detection Test (Phase 3)...")
    
    # 1. Simulate an anomaly in Cassandra
    # (Product #101 with 120 units sold - Threshold is > 50)
    settings = get_settings().extract.cassandra
    repo = get_repository("cassandra", **vars(settings))
    
    anomalous_sale = {
        "product_id": 101,
        "ds": int(time.time() * 1000),
        "transaction_id": uuid.uuid4(),
        "quantity": float(120.0),
        "price_at_sale": float(45.0),
        "channel": "API_Bulk"
    }
    
    try:
        with repo:
            logger.info("Inserting anomalous record into Cassandra 'sales'...")
            repo.add_record("sales", anomalous_sale)
            
            # 2. Trigger the Scan
            logger.info("Triggering AlertEngine scan...")
            triggered = AlertEngine.run_anomaly_scan()
            
            if 101 in triggered:
                logger.info("✓ Anomaly successfully detected and logged to 'system_alerts'.")
            else:
                logger.error("✗ AlertEngine failed to detect the anomaly.")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    execute()
