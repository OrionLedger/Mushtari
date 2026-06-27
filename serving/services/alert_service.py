from typing import List, Dict, Any, Optional
from repo import get_repository
from etl.config.settings import get_settings
from datetime import datetime

class AlertService:
    """
    Service for managing and retrieving system-monitored alerts from Cassandra.
    Focuses on high-velocity anomaly detection and threshold events.
    """

    @staticmethod
    def _get_repo():
        return get_repository("postgres")

    @classmethod
    def get_active_alerts(cls, severity: Optional[str] = None, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieves alerts from the PostgreSQL system_alerts registry.
        """
        repo = cls._get_repo()
        filters = {}
        if severity and severity != 'all':
            filters["severity"] = severity
        if not include_resolved:
            filters["is_resolved"] = False
            
        rows = repo.get_record("system_alerts", filters=filters)
        
        result = []
        for row in rows:
            sev = row.get("severity", "info").lower()
            style = cls._get_severity_style(sev)
            alert_ts = row.get("alert_ts")
            result.append({
                "id": str(row.get("alert_id")),
                "severity": sev,
                "ts": alert_ts.isoformat() if alert_ts else None,
                "type": row.get("event_type", "system"),
                "status": "active" if not row.get("is_resolved") else "resolved",
                "title": row.get("message", "Unknown Alert"),
                "desc": row.get("message"), # Redundant but for compatibility
                "time": cls._format_time(alert_ts),
                "level": sev,
                **style
            })
            
        return sorted(result, key=lambda x: x['ts'], reverse=True)

    @classmethod
    def mark_all_alerts_read(cls) -> bool:
        """
        Sets is_resolved = True on all unresolved alerts.
        """
        from infrastructure.logging.logger import get_logger
        logger = get_logger(__name__)
        repo = cls._get_repo()
        
        try:
            repo.update_records(
                table_name="system_alerts",
                filters={"is_resolved": False},
                updates={"is_resolved": True},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark all alerts as resolved: {e}")
            return False

    @classmethod
    def resolve_alert(cls, alert_id: str, severity: str = None, alert_ts: str = None) -> bool:
        """
        Updates the is_resolved status of an alert in PostgreSQL.
        """
        from infrastructure.logging.logger import get_logger
        logger = get_logger(__name__)
        repo = cls._get_repo()
        
        try:
            # In Postgres, we use alert_id (UUID) as the unique identifier
            ok = repo.update_record(
                table_name="system_alerts",
                record_id=alert_id,
                updates={"is_resolved": True},
                id_column="alert_id"
            )
            return ok
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id} in Postgres: {e}")
            return False

    @staticmethod
    def _get_severity_style(severity: str) -> Dict[str, str]:
        """Provides visual metadata for the frontend based on severity level."""
        if severity == "critical":
            return {"icon": "🔴", "color": "#ef4444", "bg": "#ef444412", "border": "#ef444430"}
        if severity == "warning":
            return {"icon": "🟡", "color": "#f59e0b", "bg": "#f59e0b12", "border": "#f59e0b30"}
        return {"icon": "🔵", "color": "#3b82f6", "bg": "#3b82f612", "border": "#3b82f630"}

    @staticmethod
    def _format_time(ts: datetime) -> str:
        """Simple human-readable time formatter."""
        if not ts: return "Just now"
        return ts.strftime("%H:%M") # Simplify for dashboard
