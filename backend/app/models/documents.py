from enum import Enum
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"
    NO_EXTRACTABLE_TEXT = "NO_EXTRACTABLE_TEXT"

class UserDocument(BaseModel):
    document_id: str
    user_id: str
    original_filename: str
    safe_filename: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus = DocumentStatus.UPLOADED
    chunk_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    indexed_at: str | None = None
    error_message: str | None = None

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    user_id: str
    text: str
    page_number: int | None = 1
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DocumentListResponse(BaseModel):
    documents: list[UserDocument] = Field(default_factory=list)

class DocumentResponse(BaseModel):
    document: UserDocument
