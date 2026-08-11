from fastapi import FastAPI
from backend.app.api.routes.triage import router as triage_router

app = FastAPI(
    title="FreshBite AI - Member 1 Triage Service",
    version="0.1.0",
)

app.include_router(triage_router)

@app.get("/health")
def health():
    return {"status": "ok"}
