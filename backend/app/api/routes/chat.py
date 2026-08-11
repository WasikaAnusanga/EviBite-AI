from fastapi import APIRouter
from backend.app.models.messages import ChatRequest, ChatResponse
from backend.app.orchestration.orchestrator import run_orchestration

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    return run_orchestration(request)
