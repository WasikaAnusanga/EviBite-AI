"""Session Conversation Memory Store for EviBite AI.

Maintains multi-turn conversation history and last-mentioned product entities per session_id.
Allows Triage Agent to resolve pronouns ('its', 'it', 'this') and Response Agent to maintain
conversational continuity like ChatGPT.
"""

from typing import Any
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    products: list[dict[str, Any]] = Field(default_factory=list)


class SessionState(BaseModel):
    session_id: str
    turns: list[ChatTurn] = Field(default_factory=list)
    last_mentioned_products: list[dict[str, Any]] = Field(default_factory=list)


class SessionMemoryStore:
    """In-memory store for session conversation states."""

    def __init__(self, max_history_turns: int = 10):
        self.max_turns = max_history_turns
        self._sessions: dict[str, SessionState] = {}

    def get_or_create_session(self, session_id: str | None) -> SessionState:
        sid = session_id or "default-session"
        if sid not in self._sessions:
            self._sessions[sid] = SessionState(session_id=sid)
        return self._sessions[sid]

    def add_user_turn(self, session_id: str | None, content: str) -> None:
        session = self.get_or_create_session(session_id)
        session.turns.append(ChatTurn(role="user", content=content))
        if len(session.turns) > self.max_turns * 2:
            session.turns = session.turns[-self.max_turns * 2 :]

    def add_assistant_turn(
        self,
        session_id: str | None,
        content: str,
        products: list[dict[str, Any]] | None = None,
    ) -> None:
        session = self.get_or_create_session(session_id)
        prod_list = products or []
        session.turns.append(ChatTurn(role="assistant", content=content, products=prod_list))

        if prod_list:
            session.last_mentioned_products = prod_list

        if len(session.turns) > self.max_turns * 2:
            session.turns = session.turns[-self.max_turns * 2 :]

    def get_last_products(self, session_id: str | None) -> list[dict[str, Any]]:
        session = self.get_or_create_session(session_id)
        return session.last_mentioned_products

    def get_formatted_history(self, session_id: str | None, max_turns: int = 6) -> list[dict[str, str]]:
        session = self.get_or_create_session(session_id)
        recent = session.turns[-max_turns:]
        return [{"role": t.role, "content": t.content} for t in recent]


# Global session memory singleton instance
session_memory = SessionMemoryStore()
