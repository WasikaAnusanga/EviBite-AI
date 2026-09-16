from fastapi import APIRouter, HTTPException

from backend.app.models.messages import ChatRequest, ChatResponse
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.security.input_sanitization import sanitize_message

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    result = sanitize_message(request.message)

    if not result.is_safe:
        raise HTTPException(
            status_code=400,
            detail="Your message could not be processed. Please rephrase your question about a product.",
        )

    # Use the cleaned text (control characters stripped) going forward,
    # not the original raw message.
    request.message = result.cleaned_message

    return run_orchestration(request)