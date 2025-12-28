from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime

class RedactionInfo(BaseModel):
    placeholder: str
    entity_type: str
    source: Literal["pii", "secret"]

class ReviewChunk(BaseModel):
    chunk_id: str
    document_id: str
    redacted_text: str
    redactions: List[RedactionInfo]
    status: Literal["pending", "approved", "rejected"]

class ReviewQueueResponse(BaseModel):
    chunks: List[ReviewChunk]
    total_count: int
