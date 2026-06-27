from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from serving.services.metric_calc import MetricCalc
from serving.services.insight_factory import InsightFactory
from serving.services.catalog_service import CatalogService
from serving.services.alert_service import AlertService
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/kpis")
async def get_kpis():
    """
    Returns high-level business KPIs aggregated via the Hybrid MetricCalc service.
    """
    try:
        return await run_in_threadpool(MetricCalc.get_business_kpis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")

@router.get("/demand")
async def get_demand_aggregation(scope: str = "week"):
    """
    Returns aggregated demand data for charts based on temporal scope.
    """
    try:
        return await run_in_threadpool(MetricCalc.get_demand_trends, scope=scope)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@router.get("/breakdown")
async def get_breakdown(category: str = "product"):
    """
    Returns revenue breakdown by product or broader categories from both DBs.
    """
    try:
        return await run_in_threadpool(MetricCalc.get_revenue_breakdown, category=category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breakdown retrieval failed: {str(e)}")

@router.get("/users")
async def get_user_stats(category: str = "device"):
    """
    Returns user acquisition statistics (device or source).
    """
    try:
        return await run_in_threadpool(MetricCalc.get_user_stats, category=category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User stats failed: {str(e)}")

@router.get("/inventory")
async def get_inventory(query: str = ""):
    """
    Fetches real SKUs and their inventory health by joining Postgres and Cassandra data.
    """
    try:
        return await run_in_threadpool(MetricCalc.get_inventory_status, query=query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory fetch failed: {str(e)}")

@router.get("/reports")
async def get_reports():
    """
    Retrieves archived documents from the persistent PostgreSQL registry.
    """
    try:
        return await run_in_threadpool(InsightFactory.get_historical_reports)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reports retrieval failed: {str(e)}")

@router.get("/library")
async def get_library(category: Optional[str] = Query(None)):
    """
    Exposes high-level insights archived in the Insight Library.
    """
    try:
        return await run_in_threadpool(InsightFactory.get_library_insights, category=category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights retrieval failed: {str(e)}")

@router.get("/products")
async def list_products(category_id: Optional[int] = None):
    """
    Lists active SKUs from the relational catalog.
    """
    try:
        return await run_in_threadpool(CatalogService.get_products, category_id=category_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product retrieval failed: {str(e)}")

from pydantic import BaseModel

class AlertResolvePayload(BaseModel):
    alert_id: str
    severity: str
    ts: str

@router.get("/alerts")
async def get_alerts(severity: Optional[str] = Query(None), include_resolved: bool = Query(False)):
    """
    Retrieves live system anomaly alerts.
    """
    try:
        return await run_in_threadpool(AlertService.get_active_alerts, severity=severity, include_resolved=include_resolved)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alerts retrieval failed: {str(e)}")

@router.post("/alerts/mark-all-read")
async def mark_all_alerts_read():
    """
    Marks all unresolved alerts as resolved.
    """
    try:
        ok = await run_in_threadpool(AlertService.mark_all_alerts_read)
        if not ok:
            raise Exception("Failed to mark all alerts as resolved")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/resolve")
async def resolve_alert(payload: AlertResolvePayload):
    """
    Marks a specific alert as resolved in the Cassandra ledger.
    """
    try:
        ok = await run_in_threadpool(AlertService.resolve_alert, 
                                     alert_id=payload.alert_id, 
                                     severity=payload.severity, 
                                     alert_ts=payload.ts)
        if not ok:
            raise Exception("Cassandra update failed")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReportGeneratePayload(BaseModel):
    name: str = "New_Report"
    type: str = "PDF"

@router.post("/reports")
async def generate_report_api(payload: ReportGeneratePayload):
    """
    Triggers on-demand report generation and archives it in the PostgreSQL registry.
    """
    try:
        import datetime
        report_meta = {
            "name": f"{payload.name}.{payload.type.lower()}",
            "report_type": payload.type,
            "file_size_kb": 1200,
            "file_path": f"/reports/{payload.name.replace(' ', '_')}.{payload.type.lower()}"
        }
        await run_in_threadpool(InsightFactory.register_report, report_meta=report_meta)
        return {"ok": True, "report": report_meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reports/{report_id}")
async def delete_report_api(report_id: int):
    """
    Removes a report from the relational registry.
    """
    try:
        ok = await run_in_threadpool(InsightFactory.delete_report, report_id=report_id)
        return {"ok": ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
