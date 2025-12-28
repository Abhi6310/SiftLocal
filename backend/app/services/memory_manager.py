from enum import Enum
from typing import Optional
from app.services import file_handler

class DocumentState(Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    SANITIZING = "sanitizing"
    SANITIZED = "sanitized"
    COMPLETED = "completed"
    ERROR = "error"

#state tracking per document
_document_states: dict[str, DocumentState] = {}
#raw extracts (parsed text/metadata) - separate from file bytes
_raw_extracts: dict[str, dict] = {}

def store_raw_extract(doc_id: str, extract: dict) -> None:
    _raw_extracts[doc_id] = extract

def get_raw_extract(doc_id: str) -> Optional[dict]:
    return _raw_extracts.get(doc_id)

def clear_raw_extract(doc_id: str) -> None:
    if doc_id in _raw_extracts:
        del _raw_extracts[doc_id]

def get_document_state(doc_id: str) -> Optional[DocumentState]:
    return _document_states.get(doc_id)

def set_document_state(doc_id: str, state: DocumentState) -> None:
    _document_states[doc_id] = state

def transition_state(doc_id: str, new_state: DocumentState) -> None:
    #lifecycle hooks on state transitions
    if new_state == DocumentState.PARSED:
        #file bytes no longer needed after parsing
        file_handler.clear_file_content(doc_id)
    elif new_state == DocumentState.SANITIZED:
        #raw extract no longer needed after sanitization
        clear_raw_extract(doc_id)
    _document_states[doc_id] = new_state

def cleanup_document(doc_id: str) -> None:
    file_handler.clear_file_content(doc_id)
    clear_raw_extract(doc_id)
    if doc_id in _document_states:
        del _document_states[doc_id]

def get_memory_stats() -> dict:
    return {
        "file_contents_count": len(file_handler._file_contents),
        "raw_extracts_count": len(_raw_extracts),
        "document_states_count": len(_document_states)
    }

def clear_all() -> None:
    _document_states.clear()
    _raw_extracts.clear()
