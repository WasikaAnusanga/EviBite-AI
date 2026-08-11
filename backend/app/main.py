from fastapi import FastAPI
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.triage import router as triage_router

app = FastAPI(
    title="EviBite AI - Backend API",
    version="0.1.0",
    description="Multi-Agent Supermarket Product Intelligence Assistant (Member 1 Orchestration & Triage)",
)

app.include_router(triage_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
