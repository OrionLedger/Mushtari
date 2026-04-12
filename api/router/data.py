from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from api.models.data_models import ETLRequestPayload

# We import the core flow from the local ETL module allowing direct mapping execution
from etl.flows.etl_flow import etl_pipeline_flow

router = APIRouter(prefix="/api/data", tags=["Data & ETL"])

@router.post("/extract")
async def trigger_etl_extraction(payload: ETLRequestPayload, background_tasks: BackgroundTasks):
    """
    Trigger the main Moshtari ETL Pipeline.
    Since ETL runs can be exceedingly heavy relying on database reads, 
    this immediately delegates work efficiently utilizing FastAPI background tasks natively.
    """
    try:
        kwargs_payload = payload.model_dump()
        
        # Fire off the heavy computation workflow decoupled utilizing BackgroundTasks
        background_tasks.add_task(
            etl_pipeline_flow,
            **kwargs_payload
        )
        
        return {
            "status": "processing",
            "message": f"ETL Pipeline extraction hook active running in background processes for source '{payload.source_type}'.",
            "assigned_configs": kwargs_payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed rapidly provisioning pipeline target: {str(e)}")
