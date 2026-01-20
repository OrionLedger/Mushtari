from fastapi import FastAPI
from src.api.router.ml import router as ml_router

app = FastAPI()
app.include_router(ml_router)