from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.app.models.messages import ChatRequest, ChatResponse
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.security.input_sanitization import sanitize_message
from backend.app.db.chat_repository import chat_repo
from backend.app.orchestration.session_memory import session_memory

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    if not request.user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to chat with EviBite AI.",
        )

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


@router.get("/chat/sessions")
def get_user_sessions(user_id: str = Query(..., description="ID or email of the user")):
    """Get all saved chat sessions for a specific user from MongoDB."""
    sessions = chat_repo.get_user_sessions(user_id)
    return {"sessions": sessions}


@router.get("/chat/sessions/{session_id}")
def get_session_history(session_id: str, user_id: Optional[str] = Query(None)):
    """Fetch history of a specific session and sync into session memory."""
    session_doc = chat_repo.get_session_by_id(session_id, user_id)
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Sync messages into in-memory session store for continued reasoning context
    messages = session_doc.get("messages", [])
    if messages:
        session_memory.load_history(session_id, messages)

    return session_doc


@router.delete("/chat/sessions/{session_id}")
def delete_session(session_id: str, user_id: Optional[str] = Query(None)):
    """Delete a chat session for a user."""
    success = chat_repo.delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    return {"status": "deleted", "session_id": session_id}