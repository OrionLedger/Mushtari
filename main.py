from contextlib import asynccontextmanager
from repo import DatabaseRegistry, get_repository
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from api.router.demand import router as demand_router
from api.router.kpi import router as kpi_router
from api.router.analytics import router as analytics_router
from api.router.sources import router as sources_router
from api.router.imports import router as imports_router

from serving.services.sync_scheduler import SyncScheduler
from fastapi.staticfiles import StaticFiles
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # PRE-CONNECT: Ensure primary DB is available at startup
    try:
        get_repository("postgres", shared=True)
    except Exception as e:
        print(f"Warning: Initial DB connection failed during startup: {e}")
        
    yield
    
    # SHUTDOWN: Cleanly close all shared connections
    DatabaseRegistry.dispose()

app = FastAPI(
    title="OrionLedger / Mushtari API",
    description="Studio-grade Backend for Advanced Demand Forecasting",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {"status": "ok", "timestamp": "now"}

app.include_router(demand_router)
app.include_router(kpi_router)
app.include_router(analytics_router)
app.include_router(sources_router)
app.include_router(imports_router)

# ── Serve frontend static build ──────────────────────────────────────
_frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.isdir(_frontend_dir):
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
    print(f"Frontend mounted at /app from {_frontend_dir}")
else:
    print(f"Warning: frontend dist not found at {_frontend_dir}")

# Instrument the app with Prometheus
Instrumentator().instrument(app).expose(app)
