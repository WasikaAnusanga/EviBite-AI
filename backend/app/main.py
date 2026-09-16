from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.triage import router as triage_router
from backend.app.security.rate_limiter import rate_limiter

app = FastAPI(
    title="EviBite AI - Backend API",
    version="0.1.0",
    description="Multi-Agent Supermarket Product Intelligence Assistant (Member 1 Orchestration & Triage)",
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Identify the caller by IP. In this dev setup everyone hits the API
    # from the same machine, so this is mainly demonstrating the pattern --
    # it becomes meaningful once deployed with real distinct clients.
    client_id = request.client.host if request.client else "unknown"

    if not rate_limiter.check(client_id):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down and try again shortly."},
        )

    return await call_next(request)


app.include_router(triage_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}