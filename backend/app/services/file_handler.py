import hashlib
import uuid
from pathlib import Path
from typing import Optional
from app.models.documents import ALLOWED_EXTENSIONS, DocumentInfo

#in-memory document store (I4: no persistence)
_documents: dict[str, dict] = {}
#in-memory file content store (cleared after parsing)
_file_contents: dict[str, bytes] = {}

def validate_file_type(filename: str) -> tuple[bool, str]:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    return True, ext

def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def store_document(filename: str, content: bytes, file_type: str) -> DocumentInfo:
    doc_id = str(uuid.uuid4())
    sha256 = compute_sha256(content)
    doc = {
        "document_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "sha256": sha256,
        "size": len(content),
        "status": "uploaded"
    }
    _documents[doc_id] = doc
    _file_contents[doc_id] = content
    return DocumentInfo(**doc)

def get_document(doc_id: str) -> Optional[DocumentInfo]:
    doc = _documents.get(doc_id)
    if doc:
        return DocumentInfo(**doc)
    return None

def get_file_content(doc_id: str) -> Optional[bytes]:
    return _file_contents.get(doc_id)

def clear_file_content(doc_id: str):
    if doc_id in _file_contents:
        del _file_contents[doc_id]

def update_document_status(doc_id: str, status: str):
    if doc_id in _documents:
        _documents[doc_id]["status"] = status

def list_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**doc) for doc in _documents.values()]

def clear_all():
    _documents.clear()
    _file_contents.clear()
