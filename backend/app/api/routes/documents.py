from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from backend.app.security.auth import get_current_user
from backend.app.models.documents import (
    UserDocument,
    DocumentListResponse,
    DocumentResponse,
)
from backend.app.services.document_service import (
    save_user_document,
    get_user_documents,
    get_user_document_by_id,
    delete_user_document,
    reindex_user_document,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a document to the authenticated user's personal document collection."""
    user_id = current_user["id"]
    filename = file.filename or "uploaded_file"

    try:
        content_bytes = await file.read()
        doc = save_user_document(
            user_id=user_id,
            content_bytes=content_bytes,
            original_filename=filename,
            content_type=file.content_type,
        )
        return DocumentResponse(document=doc)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading document: {e}",
        )


@router.get("", response_model=DocumentListResponse)
def list_documents(current_user: dict = Depends(get_current_user)):
    """Fetch all stored documents for the authenticated user."""
    user_id = current_user["id"]
    docs = get_user_documents(user_id)
    return DocumentListResponse(documents=docs)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch a specific document's metadata by ID for the authenticated user."""
    user_id = current_user["id"]
    doc = get_user_document_by_id(user_id, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )
    return DocumentResponse(document=doc)


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a document and its stored chunks for the authenticated user."""
    user_id = current_user["id"]
    success = delete_user_document(user_id, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )
    return {"status": "DELETED", "document_id": document_id}


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Re-extract and re-index a document for the authenticated user."""
    user_id = current_user["id"]
    doc = reindex_user_document(user_id, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )
    return DocumentResponse(document=doc)
