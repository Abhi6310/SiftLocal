from typing import List, Optional, Dict, Any
from app.services.memory_manager import get_sanitized_content, list_sanitized_documents
from app.services.review_manager import get_chunk_status, list_approved_chunks

class InjectionNotEligibleError(Exception):
    def __init__(self, chunk_id: str, reason: str):
        self.chunk_id = chunk_id
        self.reason = reason
        super().__init__(f"Chunk {chunk_id} not eligible: {reason}")

def is_eligible(chunk_id: str) -> bool:
    #only approved chunks can be injected
    status = get_chunk_status(chunk_id)
    if status != "approved":
        return False
    #chunk must exist in sanitized content
    if get_sanitized_content(chunk_id) is None:
        return False
    return True

def require_eligible(chunk_id: str) -> None:
    #raises InjectionNotEligibleError if chunk is not eligible
    #check existence first
    if get_sanitized_content(chunk_id) is None:
        raise InjectionNotEligibleError(chunk_id, "chunk does not exist")
    status = get_chunk_status(chunk_id)
    if status == "pending":
        raise InjectionNotEligibleError(chunk_id, "chunk is pending review")
    if status == "rejected":
        raise InjectionNotEligibleError(chunk_id, "chunk was rejected")

def get_eligible_content(chunk_id: str):
    #returns sanitized content only if approved, else raises
    require_eligible(chunk_id)
    return get_sanitized_content(chunk_id)

def get_all_eligible() -> List[str]:
    #returns list of all chunk ids that are eligible for injection
    return list_approved_chunks()

def get_eligible_contents() -> Dict[str, Any]:
    #returns dict of chunk_id -> sanitized content for all eligible chunks
    eligible_ids = get_all_eligible()
    return {
        chunk_id: get_sanitized_content(chunk_id)
        for chunk_id in eligible_ids
        if get_sanitized_content(chunk_id) is not None
    }

def get_eligibility_summary() -> Dict[str, Any]:
    #returns summary of eligibility status for all chunks
    all_docs = list_sanitized_documents()
    eligible = []
    pending = []
    rejected = []
    for doc_id in all_docs:
        status = get_chunk_status(doc_id)
        if status == "approved":
            eligible.append(doc_id)
        elif status == "rejected":
            rejected.append(doc_id)
        else:
            pending.append(doc_id)
    return {
        "eligible_count": len(eligible),
        "pending_count": len(pending),
        "rejected_count": len(rejected),
        "eligible_ids": eligible
    }
