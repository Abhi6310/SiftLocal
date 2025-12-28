import hashlib
import re
from typing import Set, Optional
from pydantic import BaseModel

#document content fingerprints for tracking
_document_hashes: Set[str] = set()
_document_substrings: Set[str] = set()
_redaction_placeholders: Set[str] = set()

#minimum substring length to track (too short = false positives)
MIN_SUBSTRING_LEN = 20
#max freeform text size allowed in LLM payload (chars)
MAX_FREEFORM_TEXT = 2000
#minimum confidence to reject (substring match ratio)
SUBSTRING_MATCH_THRESHOLD = 0.8

class GateViolation(BaseModel):
    violation_type: str
    detail: str

class GateResult(BaseModel):
    allowed: bool
    violation: Optional[GateViolation] = None

def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _extract_substrings(text: str, min_len: int = MIN_SUBSTRING_LEN) -> Set[str]:
    #extract meaningful substrings from text
    #split on whitespace and newlines, take chunks of min_len or more
    substrings = set()
    #normalize whitespace
    normalized = ' '.join(text.split())
    #sliding window for significant chunks
    words = normalized.split()
    for i in range(len(words)):
        chunk = ''
        for j in range(i, len(words)):
            chunk = ' '.join(words[i:j+1])
            if len(chunk) >= min_len:
                substrings.add(chunk.lower())
                if len(chunk) > 100:
                    break
    return substrings

def register_document_content(text: str) -> None:
    #register document text for gate tracking
    if not text or len(text.strip()) == 0:
        return
    _document_hashes.add(_compute_hash(text))
    #add significant substrings
    substrings = _extract_substrings(text)
    _document_substrings.update(substrings)

def register_redaction_placeholder(placeholder: str) -> None:
    #track redaction placeholders (e.g. [EMAIL_ADDRESS_1])
    if placeholder:
        _redaction_placeholders.add(placeholder)

def register_from_redaction_map(redaction_map) -> None:
    #register both original text and track placeholders
    if hasattr(redaction_map, 'original_text'):
        register_document_content(redaction_map.original_text)
    if hasattr(redaction_map, 'entities'):
        for entity in redaction_map.entities:
            if hasattr(entity, 'placeholder') and entity.placeholder:
                register_redaction_placeholder(entity.placeholder)
            if hasattr(entity, 'original_text') and entity.original_text:
                #register PII/secret values themselves
                if len(entity.original_text) >= 8:
                    _document_substrings.add(entity.original_text.lower())

def _check_exact_hash_match(text: str) -> bool:
    return _compute_hash(text) in _document_hashes

def _check_substring_match(text: str) -> Optional[str]:
    #check if text contains any registered document substrings
    text_lower = text.lower()
    for substring in _document_substrings:
        if substring in text_lower:
            return substring
    return None

def _check_placeholder_pattern(text: str) -> Optional[str]:
    #check for redaction placeholder patterns
    for placeholder in _redaction_placeholders:
        if placeholder in text:
            return placeholder
    #also check generic placeholder pattern
    pattern = r'\[[A-Z_]+_\d+\]'
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

def _check_freeform_text_size(text: str) -> bool:
    #reject suspiciously large freeform text
    return len(text) > MAX_FREEFORM_TEXT

def validate_llm_payload(payload: dict) -> GateResult:
    #validate entire LLM payload
    #check all string values in payload recursively
    def check_value(val, path: str = "") -> Optional[GateViolation]:
        if isinstance(val, str):
            #check exact hash match
            if _check_exact_hash_match(val):
                return GateViolation(
                    violation_type="document_hash_match",
                    detail=f"Payload at {path} matches registered document content"
                )
            #check substring match
            matched_substring = _check_substring_match(val)
            if matched_substring:
                return GateViolation(
                    violation_type="document_substring_match",
                    detail=f"Payload at {path} contains document text: '{matched_substring[:50]}...'"
                )
            #check placeholder patterns
            placeholder = _check_placeholder_pattern(val)
            if placeholder:
                return GateViolation(
                    violation_type="redaction_placeholder_detected",
                    detail=f"Payload at {path} contains redaction placeholder: {placeholder}"
                )
            #check freeform text size for specific fields
            if path and ('content' in path.lower() or 'text' in path.lower() or 'message' in path.lower()):
                if _check_freeform_text_size(val):
                    return GateViolation(
                        violation_type="freeform_text_too_large",
                        detail=f"Payload at {path} exceeds max freeform text size ({len(val)} > {MAX_FREEFORM_TEXT})"
                    )
        elif isinstance(val, dict):
            for k, v in val.items():
                result = check_value(v, f"{path}.{k}" if path else k)
                if result:
                    return result
        elif isinstance(val, list):
            for i, item in enumerate(val):
                result = check_value(item, f"{path}[{i}]")
                if result:
                    return result
        return None
    violation = check_value(payload)
    if violation:
        return GateResult(allowed=False, violation=violation)
    return GateResult(allowed=True)

def validate_text(text: str, context: str = "text") -> GateResult:
    #validate a single text field
    return validate_llm_payload({context: text})

def clear_registry() -> None:
    #clear all registered fingerprints (for testing)
    _document_hashes.clear()
    _document_substrings.clear()
    _redaction_placeholders.clear()

def get_registry_stats() -> dict:
    return {
        "document_hashes": len(_document_hashes),
        "document_substrings": len(_document_substrings),
        "redaction_placeholders": len(_redaction_placeholders)
    }
