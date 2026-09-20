import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from backend.app.models.messages import ChatRequest, ChatResponse
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.security.input_sanitization import sanitize_message
from backend.app.security.auth import get_current_user
from backend.app.db.database import get_db

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    result = sanitize_message(request.message)

    if not result.is_safe:
        raise HTTPException(
            status_code=400,
            detail="Your message could not be processed. Please rephrase your question about a product.",
        )

    # Assign authenticated user_id to request context
    request.user_id = current_user["id"]

    # Run AI multi-agent orchestration
    response = run_orchestration(request)

    # Save conversation turn to MongoDB
    user_id = current_user["id"]
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    session_id = request.session_id or str(uuid.uuid4())
    response.session_id = session_id

    # Create or update chat session
    db.chat_sessions.update_one(
        {"_id": session_id, "user_id": user_id},
        {
            "$setOnInsert": {
                "_id": session_id,
                "user_id": user_id,
                "title": request.message[:40] + ("..." if len(request.message) > 40 else ""),
                "created_at": now_iso,
            },
            "$set": {"updated_at": now_iso},
        },
        upsert=True,
    )

    # Save User message
    db.chat_messages.insert_one({
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": user_id,
        "sender": "user",
        "message": request.message,
        "timestamp": now_iso,
    })

    # Save Assistant response message
    db.chat_messages.insert_one({
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": user_id,
        "sender": "assistant",
        "message": response.final_response,
        "triage_output": response.triage_output,
        "trace_id": response.trace_id,
        "timestamp": response.timestamp,
    })

    return response