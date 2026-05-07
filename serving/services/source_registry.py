"""
serving/services/source_registry.py

Manages data source connections registered through the UI.
Persists connection metadata in Postgres and validates live connectivity.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from infrastructure.logging.logger import get_logger
from repo import get_repository
from etl.config.settings import get_settings

logger = get_logger("SourceRegistry")


class SourceRegistry:
    """CRUD + connection-test operations for the data_sources table."""

    @staticmethod
    def _get_repo(conn_uri: Optional[str] = None):
        """Returns a repository based on the connection URI or defaults to internal Postgres."""
        if not conn_uri:
            return get_repository("postgres")
            
        uri_lower = conn_uri.lower().strip()
        if uri_lower.startswith(("postgresql://", "postgres://")):
            return get_repository("postgres", connection_uri=conn_uri)
        elif "cassandra" in uri_lower:
            # Simple heuristic for cassandra hosts
            host = conn_uri.replace("cassandra://", "").split("/")[0].split(":")[0]
            if not host: host = "localhost"
            return get_repository("cassandra", contact_points=[host])
            
        # If a URI was provided but no protocol matched, raise an error instead of defaulting
        raise ValueError(f"Unsupported or malformed database URI: {conn_uri}")

    # ── List ──────────────────────────────────────────────────────────────────
    @classmethod
    def list_sources(cls) -> List[Dict[str, Any]]:
        repo = cls._get_repo()
        rows = repo.get_record("data_sources")
        result = []
        for r in rows:
            result.append({
                "id":             r["id"],
                "name":           r["name"],
                "type":           r["source_type"],
                "uri":            r["conn_uri"],
                "status":         r["status"],
                "source_table":   r.get("source_table"),
                "column_mapping": r.get("column_mapping", {}),
                "last_sync":      _fmt_ts(r.get("last_synced"))
            })
        return result

    # ── CRUD ──────────────────────────────────────────────────────────────────
    @classmethod
    def add_source(cls, name: str, source_type: str, uri: str, table_name: Optional[str] = None) -> bool:
        repo = cls._get_repo()
        record = {
            "name":           name.strip(),
            "source_type":    source_type.strip(),
            "conn_uri":       uri.strip(),
            "status":         "Active",
            "source_table":   table_name,
            "column_mapping": {}
        }
        return repo.add_record("data_sources", record)

    @classmethod
    def update_mapping(cls, source_id: int, table_name: str, mapping: Dict[str, str]) -> bool:
        """Update the physical table name and column mapping for a source."""
        repo = cls._get_repo()
        return repo.update_record(
            "data_sources", 
            source_id, 
            {"source_table": table_name, "column_mapping": mapping}
        )

    @classmethod
    def delete_source(cls, source_id: int) -> bool:
        repo = cls._get_repo()
        return repo.delete_record("data_sources", source_id)

    # ── Inspection ────────────────────────────────────────────────────────────
    @classmethod
    def get_source_tables(cls, conn_uri: str) -> List[str]:
        """Discovery: Lists all tables available in the source database."""
        try:
            repo = cls._get_repo(conn_uri)
            if not repo.is_connected():
                repo.connect()
            return repo.get_tables()
        except Exception as e:
            logger.error(f"Table discovery failed: {e}")
            return []

    @classmethod
    def get_source_schema(cls, conn_uri: str, table_name: str) -> List[Dict[str, str]]:
        """Connects to a source and retrieves the schema for a specific table."""
        try:
            repo = cls._get_repo(conn_uri)
            if not repo.is_connected():
                repo.connect()
            
            return repo.get_table_columns(table_name)
        except Exception as e:
            logger.error(f"Schema discovery failed: {e}")
            raise

    # ── Test Connection ───────────────────────────────────────────────────────
    @classmethod
    def test_connection(cls, conn_uri: str) -> Dict[str, Any]:
        """Verify if a source is reachable by trying to connect to its repository."""
        try:
            repo = cls._get_repo(conn_uri)
            repo.connect()
            connected = repo.is_connected()
            repo.close()
            
            if connected:
                return {"ok": True, "message": "Connection successful. Source is reachable."}
            return {"ok": False, "message": "Could not establish connection."}
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return {"ok": False, "message": str(e)}

    # ── Watermarking ──────────────────────────────────────────────────────────
    @classmethod
    def get_watermark(cls, source_id: int) -> Optional[datetime]:
        """Fetch the last successful sync timestamp for a source."""
        repo = cls._get_repo()
        rows = repo.get_record("sync_watermarks", filters={"source_id": source_id})
        if rows:
            return rows[0]["last_synced_at"]
        return None

    @classmethod
    def update_watermark(cls, source_id: int, rows_synced: int, duration: float):
        """Persist sync metadata and advance the watermark."""
        repo = cls._get_repo()
        record = {
            "source_id": source_id,
            "last_synced_at": datetime.now(),
            "rows_synced": rows_synced,
            "sync_duration_s": duration,
            "updated_at": datetime.now()
        }
        # Check if exists
        exists = repo.get_record("sync_watermarks", filters={"source_id": source_id})
        if exists:
            repo.update_record("sync_watermarks", source_id, record, id_column="source_id")
        else:
            repo.add_record("sync_watermarks", record)

    # ── Sync Now ──────────────────────────────────────────────────────────────
    @classmethod
    def sync_source(cls, source_id: int) -> Dict[str, Any]:
        """
        Triggers an ETL extraction using the source's registered mapping.
        Now defaults to 'orders' mode with incremental watermarking.
        """
        from etl.flows.etl_flow import etl_pipeline_flow
        import time

        repo = cls._get_repo()
        rows = repo.get_record("data_sources", filters={"id": source_id})

        if not rows:
            return {"ok": False, "message": "Source not found."}

        source = rows[0]
        conn_uri = source["conn_uri"].strip()
        source_type = source["source_type"]
        target_table = source.get("source_table")
        mapping = source.get("column_mapping", {})
        
        if not target_table:
            return {"ok": False, "message": "No table mapped for this source."}

        # 1. Determine Watermark
        watermark = cls.get_watermark(source_id)
        watermark_str = watermark.isoformat() if watermark else None

        # 2. Map UI source_type → ETL choices
        db_type = "postgres"
        if "cassandra" in conn_uri.lower():
            db_type = "cassandra"

        start_time = time.time()
        try:
            result = etl_pipeline_flow(
                source_type="database",
                source_config={
                    "table_name": target_table, 
                    "db_type": db_type, 
                    "uri": conn_uri
                },
                column_mapping=mapping,
                load_to_db=True,
                db_type="postgres", # Final destination is always Postgres in order mode
                pipeline_mode="orders",
                source_id=source_id,
                items_source_type=source.get("items_source_type", "json_column"),
                watermark=watermark_str,
                track_in_mlflow=False,
            )

            # 3. Update Status and Watermark
            duration = time.time() - start_time
            rows_synced = result.get("load", {}).get("inserted", 0)
            
            repo.update_record("data_sources", source_id, {
                "status": "active", 
                "last_synced": datetime.now()
            })
            
            cls.update_watermark(source_id, rows_synced, duration)

            return {
                "ok": True, 
                "status": result.get("status"), 
                "rows": rows_synced,
                "duration": round(duration, 2)
            }

        except Exception as e:
            logger.error(f"Sync failed for source {source_id}: {e}")
            repo.update_record("data_sources", source_id, {"status": "error"})
            return {"ok": False, "message": str(e)}


def _fmt_ts(ts) -> str:
    if not ts:
        return "Never"
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M")
    return str(ts)
