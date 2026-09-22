from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    trace_id: str
    from_agent: str
    to_agent: str
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, max_length=100)
    user_id: str | None = Field(default=None, max_length=100)


class ExecutionStep(BaseModel):
    agent: str
    action: str
    status: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatResponse(BaseModel):
    trace_id: str
    session_id: str | None = None
    query: str
    execution_path: list[str] = Field(default_factory=list)
    execution_steps: list[ExecutionStep] = Field(default_factory=list)
    triage_output: dict[str, Any]
    final_response: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
