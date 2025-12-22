from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.documents import UploadResponse, DocumentInfo
from app.services.file_handler import validate_file_type, store_document, get_document, list_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    valid, result = validate_file_type(file.filename or "")
    if not valid:
        raise HTTPException(status_code=400, detail=result)
    file_type = result
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    doc = store_document(file.filename or "unknown", content, file_type)
    return UploadResponse(
        document_id=doc.document_id,
        filename=doc.filename,
        file_type=doc.file_type,
        sha256=doc.sha256,
        size=doc.size
    )

@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_info(document_id: str):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/", response_model=list[DocumentInfo])
async def list_all_documents():
    return list_documents()
