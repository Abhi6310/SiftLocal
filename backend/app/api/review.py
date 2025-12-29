from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from app.models.review import ReviewChunk, ReviewQueueResponse, RedactionInfo
from app.services.memory_manager import list_sanitized_documents, get_sanitized_content
from app.services.review_manager import (
    get_chunk_status, approve_chunk, reject_chunk,
    bulk_approve, bulk_reject, get_status_counts
)

router = APIRouter(prefix="/api/review", tags=["review"])

class ActionResponse(BaseModel):
    success: bool
    chunk_id: str
    status: str

class BulkActionRequest(BaseModel):
    chunk_ids: List[str]

class BulkActionResponse(BaseModel):
    results: dict
    success_count: int
    failure_count: int

class StatusCountsResponse(BaseModel):
    pending: int
    approved: int
    rejected: int

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
            status=get_chunk_status(doc_id)
        ))
    return ReviewQueueResponse(chunks=chunks, total_count=len(chunks))

@router.get("/counts", response_model=StatusCountsResponse)
async def get_status_counts_endpoint():
    counts = get_status_counts()
    return StatusCountsResponse(**counts)

#bulk routes must come before parameterized routes
@router.post("/bulk/approve", response_model=BulkActionResponse)
async def bulk_approve_endpoint(request: BulkActionRequest):
    results = bulk_approve(request.chunk_ids)
    success_count = sum(1 for v in results.values() if v)
    failure_count = len(results) - success_count
    return BulkActionResponse(
        results=results,
        success_count=success_count,
        failure_count=failure_count
    )

@router.post("/bulk/reject", response_model=BulkActionResponse)
async def bulk_reject_endpoint(request: BulkActionRequest):
    results = bulk_reject(request.chunk_ids)
    success_count = sum(1 for v in results.values() if v)
    failure_count = len(results) - success_count
    return BulkActionResponse(
        results=results,
        success_count=success_count,
        failure_count=failure_count
    )

#parameterized routes after specific routes
@router.post("/{chunk_id}/approve", response_model=ActionResponse)
async def approve_chunk_endpoint(chunk_id: str):
    success = approve_chunk(chunk_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ActionResponse(success=True, chunk_id=chunk_id, status="approved")

@router.post("/{chunk_id}/reject", response_model=ActionResponse)
async def reject_chunk_endpoint(chunk_id: str):
    success = reject_chunk(chunk_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ActionResponse(success=True, chunk_id=chunk_id, status="rejected")
