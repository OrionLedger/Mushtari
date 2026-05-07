"""
serving/services/alert_engine.py

Automated Alerting Engine. Scans the Cassandra fact-store for 
anomalies (e.g. sales spikes, inventory drops) and generates 
system-wide alerts.
"""

import uuid
import time
from typing import List, Dict, Any
from infrastructure.logging.logger import get_logger
from repo import get_repository
from etl.config.settings import get_settings

logger = get_logger(__name__)

class AlertEngine:
    @classmethod
    def _get_cassandra(cls):
        settings = get_settings().extract.cassandra
        return get_repository("cassandra", **vars(settings))

    @classmethod
    def _get_postgres(cls):
        settings = get_settings().extract.postgres
        return get_repository("postgres", **vars(settings))

    @classmethod
    def generate_alert(cls, severity: str, event_type: str, message: str):
        """
        Inserts a new alert record into the PostgreSQL persistent registry.
        """
        repo = cls._get_postgres()
        alert_id = uuid.uuid4()
        
        # Postgres uses TIMESTAMP (native datetime)
        from datetime import datetime
        
        record = {
            "alert_id": alert_id,
            "severity": severity, # 'critical', 'warning', 'info'
            "event_type": event_type,
            "alert_ts": datetime.now(),
            "message": message,
            "is_resolved": False
        }
        
        try:
            repo.add_record("system_alerts", record)
            logger.info(f"[Alert Engine] Generated {severity.upper()} alert in Postgres: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate alert in Postgres: {e}")
            return False

    @classmethod
    def run_anomaly_scan(cls):
        """
        Data-driven anomaly scan. Compares recent Cassandra sales 
        against product-specific safety thresholds in PostgreSQL.
        """
        c_repo = cls._get_cassandra()
        p_repo = get_repository("postgres", **vars(get_settings().extract.postgres))
        
        logger.info("Starting Data-Driven Anomaly Scan...")
        
        try:
            with c_repo:
                # 1. Fetch sales anomalies (Spikes) from Cassandra
                rows = c_repo.get_record("sales", columns=["product_id", "quantity"])
                
                # 2. Fetch safety thresholds from PostgreSQL
                products = p_repo.get_record("products", columns=["id", "safety_stock", "name"])
                safety_map = {p['id']: p['safety_stock'] for p in products}
                
                triggered = []
                for row in rows:
                    pid = row['product_id']
                    threshold = safety_map.get(pid, 20) # fallback
                    
                    # If current transaction quantity > 3x safety_stock, flag as spike
                    if float(row['quantity']) > (threshold * 3):
                        if pid not in triggered:
                            triggered.append(pid)
                            cls.generate_alert(
                                severity="critical" if row['quantity'] > 100 else "warning",
                                event_type="SALES_VOLUME_SPIKE",
                                message=f"Anomaly: Product '{pid}' sales velocity exceeds safety threshold ({row['quantity']} units)."
                            )
                
                if not triggered:
                    logger.info("Audit complete. No operational anomalies detected.")
                return triggered
        except Exception as e:
            logger.error(f"Anomaly scan failed: {e}")
            return []
