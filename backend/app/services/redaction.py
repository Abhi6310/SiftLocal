from typing import List, Dict
from datetime import datetime
from app.models.redaction import DetectedEntity, RedactionMap
from app.services.sanitizer import PIIEntity
from app.services.secret_detector import SecretEntity

def merge_entities(pii_entities: List[PIIEntity], secret_entities: List[SecretEntity]) -> List[DetectedEntity]:
    #convert to unified format
    all_entities: List[Dict] = []
    for e in pii_entities:
        all_entities.append({
            "entity_type": e.entity_type,
            "source": "pii",
            "start": e.start,
            "end": e.end,
            "confidence": e.score,
            "original_text": e.text
        })
    for e in secret_entities:
        all_entities.append({
            "entity_type": e.secret_type,
            "source": "secret",
            "start": e.start,
            "end": e.end,
            "confidence": e.confidence,
            "original_text": e.text
        })
    #sort by start position
    all_entities.sort(key=lambda x: (x["start"], -x["confidence"]))
    #resolve overlaps
    merged: List[Dict] = []
    for entity in all_entities:
        if not merged:
            merged.append(entity)
            continue
        last = merged[-1]
        #check overlap
        if entity["start"] < last["end"]:
            #overlap detected - keep higher confidence
            if entity["confidence"] > last["confidence"]:
                merged[-1] = entity
            #else keep last (higher or equal confidence)
        else:
            merged.append(entity)
    return [DetectedEntity(
        entity_type=e["entity_type"],
        source=e["source"],
        start=e["start"],
        end=e["end"],
        confidence=e["confidence"],
        original_text=e["original_text"],
        placeholder=""
    ) for e in merged]

def generate_placeholders(entities: List[DetectedEntity]) -> List[DetectedEntity]:
    #count occurrences of each type for sequential numbering
    type_counts: Dict[str, int] = {}
    result = []
    for entity in entities:
        etype = entity.entity_type
        type_counts[etype] = type_counts.get(etype, 0) + 1
        placeholder = f"[{etype}_{type_counts[etype]}]"
        result.append(DetectedEntity(
            entity_type=entity.entity_type,
            source=entity.source,
            start=entity.start,
            end=entity.end,
            confidence=entity.confidence,
            original_text=entity.original_text,
            placeholder=placeholder
        ))
    return result

def apply_redaction(text: str, entities: List[DetectedEntity]) -> str:
    if not entities:
        return text
    #sort by start position descending to replace from end first
    sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
    result = text
    for entity in sorted_entities:
        result = result[:entity.start] + entity.placeholder + result[entity.end:]
    return result

def reverse_redaction(redacted_text: str, entities: List[DetectedEntity]) -> str:
    result = redacted_text
    for entity in entities:
        result = result.replace(entity.placeholder, entity.original_text)
    return result

def generate_redaction_map(text: str, pii_entities: List[PIIEntity], secret_entities: List[SecretEntity]) -> RedactionMap:
    merged = merge_entities(pii_entities, secret_entities)
    with_placeholders = generate_placeholders(merged)
    redacted = apply_redaction(text, with_placeholders)
    return RedactionMap(
        original_text=text,
        redacted_text=redacted,
        entities=with_placeholders,
        created_at=datetime.now()
    )
