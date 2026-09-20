import os
import shutil
from uuid import uuid4
from datetime import datetime, timezone
from pymongo import ASCENDING, DESCENDING

from backend.app.db.database import get_db
from backend.app.models.documents import (
    DocumentStatus,
    UserDocument,
    DocumentChunk,
)
from backend.app.services.document_parser import (
    sanitize_filename,
    validate_upload_file,
    extract_text_by_pages,
    chunk_document_pages,
)
from backend.app.sources.user_documents import invalidate_user_index

UPLOAD_BASE_DIR = os.path.join(os.getcwd(), "uploads", "documents")


def _get_user_upload_dir(user_id: str) -> str:
    user_dir = os.path.join(UPLOAD_BASE_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def save_user_document(
    user_id: str,
    content_bytes: bytes,
    original_filename: str,
    content_type: str | None = None,
) -> UserDocument:
    """Validate, store, extract, and index a user document."""
    validate_upload_file(original_filename, content_bytes, content_type)

    safe_name = sanitize_filename(original_filename)
    document_id = f"doc-{uuid4().hex[:12]}"
    user_dir = _get_user_upload_dir(user_id)
    file_path = os.path.join(user_dir, f"{document_id}_{safe_name}")

    # Write file to isolated local disk storage
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # Extract text & chunks
    pages, status_str = extract_text_by_pages(safe_name, content_bytes)
    status = DocumentStatus(status_str)

    chunks: list[DocumentChunk] = []
    if status == DocumentStatus.READY and pages:
        chunks = chunk_document_pages(document_id, user_id, safe_name, pages)

    now_iso = datetime.now(timezone.utc).isoformat()
    doc_meta = UserDocument(
        document_id=document_id,
        user_id=user_id,
        original_filename=original_filename,
        safe_filename=safe_name,
        mime_type=content_type or "application/octet-stream",
        size_bytes=len(content_bytes),
        status=status,
        chunk_count=len(chunks),
        created_at=now_iso,
        indexed_at=now_iso if status == DocumentStatus.READY else None,
        error_message=None if status != DocumentStatus.NO_EXTRACTABLE_TEXT else "No extractable text found in file.",
    )

    db = get_db()
    # Save metadata
    doc_dict = doc_meta.model_dump()
    doc_dict["_id"] = document_id
    db.user_documents.insert_one(doc_dict)

    # Save chunks
    if chunks:
        chunk_dicts = []
        for c in chunks:
            cd = c.model_dump()
            cd["_id"] = c.chunk_id
            chunk_dicts.append(cd)
        db.document_chunks.insert_many(chunk_dicts)

    invalidate_user_index(user_id)
    return doc_meta


def get_user_documents(user_id: str) -> list[UserDocument]:
    """Fetch all documents owned by user_id."""
    db = get_db()
    cursor = db.user_documents.find({"user_id": user_id}).sort("created_at", DESCENDING)
    docs = []
    for d in cursor:
        d.pop("_id", None)
        docs.append(UserDocument.model_validate(d))
    return docs


def get_user_document_by_id(user_id: str, document_id: str) -> UserDocument | None:
    """Fetch a specific document belonging to user_id."""
    db = get_db()
    d = db.user_documents.find_one({"_id": document_id, "user_id": user_id})
    if not d:
        return None
    d.pop("_id", None)
    return UserDocument.model_validate(d)


def delete_user_document(user_id: str, document_id: str) -> bool:
    """Delete document metadata, chunks, and file for user_id."""
    db = get_db()
    doc = db.user_documents.find_one({"_id": document_id, "user_id": user_id})
    if not doc:
        return False

    # Delete metadata & chunks from Mongo
    db.user_documents.delete_one({"_id": document_id, "user_id": user_id})
    db.document_chunks.delete_many({"document_id": document_id, "user_id": user_id})

    # Delete physical file
    user_dir = _get_user_upload_dir(user_id)
    safe_name = doc.get("safe_filename", "")
    file_path = os.path.join(user_dir, f"{document_id}_{safe_name}")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    invalidate_user_index(user_id)
    return True


def reindex_user_document(user_id: str, document_id: str) -> UserDocument | None:
    """Re-extract text and reindex chunks for an existing document."""
    db = get_db()
    doc_dict = db.user_documents.find_one({"_id": document_id, "user_id": user_id})
    if not doc_dict:
        return None

    safe_name = doc_dict.get("safe_filename", "")
    user_dir = _get_user_upload_dir(user_id)
    file_path = os.path.join(user_dir, f"{document_id}_{safe_name}")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "rb") as f:
        content_bytes = f.read()

    pages, status_str = extract_text_by_pages(safe_name, content_bytes)
    status = DocumentStatus(status_str)

    db.document_chunks.delete_many({"document_id": document_id, "user_id": user_id})

    chunks: list[DocumentChunk] = []
    if status == DocumentStatus.READY and pages:
        chunks = chunk_document_pages(document_id, user_id, safe_name, pages)
        chunk_dicts = []
        for c in chunks:
            cd = c.model_dump()
            cd["_id"] = c.chunk_id
            chunk_dicts.append(cd)
        db.document_chunks.insert_many(chunk_dicts)

    now_iso = datetime.now(timezone.utc).isoformat()
    db.user_documents.update_one(
        {"_id": document_id, "user_id": user_id},
        {
            "$set": {
                "status": status.value,
                "chunk_count": len(chunks),
                "indexed_at": now_iso if status == DocumentStatus.READY else None,
                "error_message": None if status != DocumentStatus.NO_EXTRACTABLE_TEXT else "No extractable text found in file.",
            }
        },
    )

    return get_user_document_by_id(user_id, document_id)
