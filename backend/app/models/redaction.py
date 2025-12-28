from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime

class DetectedEntity(BaseModel):
    entity_type: str
    source: Literal["pii", "secret"]
    start: int
    end: int
    confidence: float
    original_text: str
    placeholder: str

class RedactionMap(BaseModel):
    original_text: str
    redacted_text: str
    entities: List[DetectedEntity]
    created_at: datetime
