from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router.demand import router as demand_router
from api.router.data import router as data_router
from api.router.kpi import router as kpi_router
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="ML API")

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

# Instrument the app with Prometheus
Instrumentator().instrument(app).expose(app)
