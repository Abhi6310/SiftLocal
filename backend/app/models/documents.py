from pydantic import BaseModel
from typing import Literal

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "text/csv", "text/plain"}
ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".csv", ".txt"}

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    sha256: str
    size: int

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    sha256: str
    size: int
    status: Literal["uploaded", "parsing", "parsed", "error"]
