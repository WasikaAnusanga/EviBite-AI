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
