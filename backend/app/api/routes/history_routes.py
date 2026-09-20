from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import DESCENDING, ASCENDING

from backend.app.db.database import get_db
from backend.app.security.auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def get_user_chat_sessions(current_user: dict = Depends(get_current_user)):
    """Fetch all chat sessions for the logged-in user."""
    db = get_db()
    user_id = current_user["id"]

    cursor = db.chat_sessions.find({"user_id": user_id}).sort("updated_at", DESCENDING)
    sessions = []
    for s in cursor:
        sessions.append({
            "session_id": str(s["_id"]),
            "title": s.get("title", "New Conversation"),
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
        })

    return {"sessions": sessions}


@router.get("/{session_id}")
def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    """Fetch all messages within a specific session for the logged-in user."""
    db = get_db()
    user_id = current_user["id"]

    # Verify session belongs to user
    session = db.chat_sessions.find_one({"_id": session_id, "user_id": user_id})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied.",
        )

    cursor = db.chat_messages.find({"session_id": session_id, "user_id": user_id}).sort("timestamp", ASCENDING)
    messages = []
    for m in cursor:
        messages.append({
            "id": str(m["_id"]),
            "session_id": m["session_id"],
            "sender": m["sender"],
            "message": m["message"],
            "triage_output": m.get("triage_output"),
            "trace_id": m.get("trace_id"),
            "timestamp": m.get("timestamp"),
        })

    return {"session": {"session_id": session_id, "title": session.get("title")}, "messages": messages}
