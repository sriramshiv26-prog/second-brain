"""Document upload and processing endpoints."""

from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel
import mimetypes
from api.synthesis_service import get_synthesis_service

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentMetadata(BaseModel):
    """Document metadata."""

    id: str
    filename: str
    content_type: str
    size: int
    uploaded_at: str


class DocumentProcessingResult(BaseModel):
    """Document processing result."""

    document_id: str
    status: str
    extracted_text: Optional[str] = None
    entities_found: int = 0
    chunks_created: int = 0


class DocumentList(BaseModel):
    """List of documents."""

    documents: List[DocumentMetadata]
    total: int


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> DocumentMetadata:
    """Upload a document (PDF, Word, PowerPoint)."""
    from datetime import datetime
    import uuid

    allowed_types = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()

    return DocumentMetadata(
        id=str(uuid.uuid4()),
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        uploaded_at=datetime.utcnow().isoformat(),
    )


@router.post("/process/{document_id}")
async def process_document(document_id: str, entities: Optional[List[dict]] = None) -> dict:
    """Process an uploaded document (extract text, entities, etc).

    NEW (Phase 6): Triggers synthesis service to auto-create wiki pages.
    """
    try:
        # Extract entities from document
        # (In production, this would call document processing pipeline)
        extracted_entities = entities or []

        # NEW: Integrate into wiki system
        synthesis_service = get_synthesis_service()
        wiki_mapping = await synthesis_service.integrate_document(
            doc_id=document_id,
            entities=extracted_entities,
            doc_title=f"Document {document_id}"
        )

        return {
            "document_id": document_id,
            "status": "processed",
            "entities_found": len(extracted_entities),
            "wiki_pages_created": wiki_mapping,
            "wiki_pages_count": len(wiki_mapping),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/list")
def list_documents() -> DocumentList:
    """List all uploaded documents."""
    return DocumentList(documents=[], total=0)


@router.get("/{document_id}")
def get_document_info(document_id: str) -> DocumentMetadata:
    """Get document information."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found",
    )


@router.delete("/{document_id}")
def delete_document(document_id: str) -> dict:
    """Delete a document."""
    return {"status": "deleted", "document_id": document_id}


@router.get("/{document_id}/text")
def get_document_text(document_id: str) -> dict:
    """Get extracted text from document."""
    return {
        "document_id": document_id,
        "text": "Extracted text would be here",
    }


@router.get("/{document_id}/entities")
def get_document_entities(document_id: str) -> dict:
    """Get entities extracted from document."""
    return {
        "document_id": document_id,
        "entities": [],
        "entity_count": 0,
    }


@router.get("/{document_id}/chunks")
def get_document_chunks(document_id: str) -> dict:
    """Get text chunks from document."""
    return {
        "document_id": document_id,
        "chunks": [],
        "chunk_count": 0,
    }
