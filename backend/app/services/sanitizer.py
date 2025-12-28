from pydantic import BaseModel
from typing import List, Optional
from presidio_analyzer import AnalyzerEngine

class PIIEntity(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    text: str

_analyzer: Optional[AnalyzerEngine] = None

def get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
    return _analyzer

def detect_pii(text: str, score_threshold: float = 0.5) -> List[PIIEntity]:
    analyzer = get_analyzer()
    results = analyzer.analyze(text=text, language="en")
    entities = []
    for result in results:
        if result.score >= score_threshold:
            entities.append(PIIEntity(
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                score=result.score,
                text=text[result.start:result.end]
            ))
    return entities
