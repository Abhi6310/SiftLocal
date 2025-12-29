from typing import Literal, List, Dict, Optional
from app.services.memory_manager import list_sanitized_documents, get_sanitized_content

ChunkStatus = Literal["pending", "approved", "rejected"]

#in-memory approval status tracking
_chunk_status: Dict[str, ChunkStatus] = {}

def get_chunk_status(chunk_id: str) -> ChunkStatus:
    return _chunk_status.get(chunk_id, "pending")

def set_chunk_status(chunk_id: str, status: ChunkStatus) -> bool:
    #verify chunk exists in sanitized content
    if not get_sanitized_content(chunk_id):
        return False
    _chunk_status[chunk_id] = status
    return True

def approve_chunk(chunk_id: str) -> bool:
    return set_chunk_status(chunk_id, "approved")

def reject_chunk(chunk_id: str) -> bool:
    return set_chunk_status(chunk_id, "rejected")

def bulk_approve(chunk_ids: List[str]) -> Dict[str, bool]:
    return {chunk_id: approve_chunk(chunk_id) for chunk_id in chunk_ids}

def bulk_reject(chunk_ids: List[str]) -> Dict[str, bool]:
    return {chunk_id: reject_chunk(chunk_id) for chunk_id in chunk_ids}

def list_approved_chunks() -> List[str]:
    #todo: returns only approved chunks eligible for injection
    return [
        chunk_id for chunk_id in list_sanitized_documents()
        if _chunk_status.get(chunk_id) == "approved"
    ]

def list_rejected_chunks() -> List[str]:
    return [
        chunk_id for chunk_id in list_sanitized_documents()
        if _chunk_status.get(chunk_id) == "rejected"
    ]

def list_pending_chunks() -> List[str]:
    return [
        chunk_id for chunk_id in list_sanitized_documents()
        if _chunk_status.get(chunk_id, "pending") == "pending"
    ]

def get_status_counts() -> Dict[str, int]:
    docs = list_sanitized_documents()
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for doc_id in docs:
        status = _chunk_status.get(doc_id, "pending")
        counts[status] += 1
    return counts

def clear_status(chunk_id: str) -> None:
    if chunk_id in _chunk_status:
        del _chunk_status[chunk_id]

def clear_all_status() -> None:
    _chunk_status.clear()
