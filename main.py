from fastapi import FastAPI
from src.api.router.ml import router  # import your router

app = FastAPI(title="ML API")

app.include_router(router)
