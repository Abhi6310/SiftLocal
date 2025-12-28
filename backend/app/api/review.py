from fastapi import APIRouter
from typing import List
from app.models.review import ReviewChunk, ReviewQueueResponse, RedactionInfo
from app.services.memory_manager import list_sanitized_documents, get_sanitized_content

router = APIRouter(prefix="/api/review", tags=["review"])

@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue():
    doc_ids = list_sanitized_documents()
    chunks: List[ReviewChunk] = []
    for doc_id in doc_ids:
        redaction_map = get_sanitized_content(doc_id)
        if not redaction_map:
            continue
        #extract redaction info for highlighting (no original text exposed)
        redactions = [
            RedactionInfo(
                placeholder=entity.placeholder,
                entity_type=entity.entity_type,
                source=entity.source
            )
            for entity in redaction_map.entities
        ]
        chunks.append(ReviewChunk(
            chunk_id=doc_id,
            document_id=doc_id,
            redacted_text=redaction_map.redacted_text,
            redactions=redactions,
            status="pending"
        ))
    return ReviewQueueResponse(chunks=chunks, total_count=len(chunks))
