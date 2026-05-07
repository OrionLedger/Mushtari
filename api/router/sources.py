"""
api/router/sources.py

REST endpoints for the Data Sources registry.
GET    /api/sources              – list all saved connections
POST   /api/sources              – save a new connection
DELETE /api/sources/{id}         – remove a connection
POST   /api/sources/test         – live connection test (no DB write)
POST   /api/sources/{id}/sync    – trigger ETL sync from this source
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool

from api.models.data_models import SourceCreatePayload, TestConnectionPayload, MappingUpdatePayload
from serving.services.source_registry import SourceRegistry

router = APIRouter(prefix="/api/sources", tags=["Data Sources"])


@router.get("")
async def list_sources():
    """Return all registered data sources."""
    try:
        return await run_in_threadpool(SourceRegistry.list_sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_source(payload: SourceCreatePayload):
    """Persist a new data source connection."""
    try:
        return await run_in_threadpool(
            SourceRegistry.add_source,
            payload.name,
            payload.source_type,
            payload.conn_uri,
            payload.table_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/tables")
async def get_source_tables(source_id: int):
    """Discovery: return all tables in the database."""
    try:
        sources = await run_in_threadpool(SourceRegistry.list_sources)
        matched = [s for s in sources if s["id"] == source_id]
        if not matched:
            raise HTTPException(status_code=404, detail="Source not found.")
        
        uri = matched[0]["uri"]
        return await run_in_threadpool(SourceRegistry.get_source_tables, uri)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/schema")
async def get_source_schema(source_id: int, table_name: str):
    """Inspect a source and return the list of columns."""
    try:
        # First get the URI from the registry
        sources = await run_in_threadpool(SourceRegistry.list_sources)
        matched = [s for s in sources if s["id"] == source_id]
        if not matched:
            raise HTTPException(status_code=404, detail="Source not found.")
        
        uri = matched[0]["uri"]
        return await run_in_threadpool(SourceRegistry.get_source_schema, uri, table_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{source_id}/mapping")
async def update_source_mapping(source_id: int, payload: MappingUpdatePayload):
    """Update the table mapping for a specific source."""
    try:
        success = await run_in_threadpool(
            SourceRegistry.update_mapping,
            source_id,
            payload.table_name,
            payload.mapping
        )
        if not success:
            raise HTTPException(status_code=404, detail="Source not found.")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}")
async def delete_source(source_id: int):
    """Remove a data source by ID."""
    try:
        deleted = await run_in_threadpool(SourceRegistry.delete_source, source_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Source not found.")
        return {"ok": True, "deleted_id": source_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_connection(payload: TestConnectionPayload):
    """
    Performs a live connection test against the supplied URI.
    Returns {ok: bool, message: str}. Does NOT persist anything.
    """
    try:
        result = await run_in_threadpool(SourceRegistry.test_connection, payload.conn_uri)
        return result
    except Exception as e:
        return {"ok": False, "message": str(e)}


@router.post("/{source_id}/sync")
async def sync_source(source_id: int, background_tasks: BackgroundTasks):
    """
    Kicks off an ETL sync job for the given source in the background.
    Returns immediately with a 202 Accepted so the UI stays responsive.
    """
    try:
        background_tasks.add_task(SourceRegistry.sync_source, source_id)
        return {
            "ok": True,
            "message": f"Sync job started for source #{source_id}.",
            "status": "syncing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all")
async def sync_all_sources():
    """Trigger parallel sync for all registered sources."""
    from serving.services.sync_scheduler import SyncScheduler
    try:
        scheduler = SyncScheduler.get_instance()
        return scheduler.sync_all_now()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
