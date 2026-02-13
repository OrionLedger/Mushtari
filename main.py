from fastapi import FastAPI
from api.router.demand import router  # import your router
from fastapi.responses import RedirectResponse

app = FastAPI(title="ML API")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(router)
