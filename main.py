from contextlib import asynccontextmanager
from repo import DatabaseRegistry, get_repository
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from api.router.demand import router as demand_router
from api.router.data import router as data_router
from api.router.kpi import router as kpi_router
from api.router.analytics import router as analytics_router
from api.router.sources import router as sources_router

from serving.services.sync_scheduler import SyncScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # PRE-CONNECT: Ensure primary DBs are available at startup
    try:
        get_repository("postgres", shared=True)
        get_repository("cassandra", shared=True)
        
        # Start background sync scheduler
        SyncScheduler.get_instance().start()
        
    except Exception as e:
        print(f"Warning: Initial DB connection failed during startup: {e}")
        
    yield
    
    # SHUTDOWN: Cleanly close all shared connections
    SyncScheduler.get_instance().stop()
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
app.include_router(data_router)
app.include_router(kpi_router)
app.include_router(analytics_router)
app.include_router(sources_router)

# Instrument the app with Prometheus
Instrumentator().instrument(app).expose(app)
