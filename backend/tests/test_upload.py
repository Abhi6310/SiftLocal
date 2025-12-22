import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.file_handler import clear_all, _documents, _file_contents

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    clear_all()
    yield
    clear_all()

def test_upload_pdf():
    content = b"%PDF-1.4 test content"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == ".pdf"
    assert data["size"] == len(content)
    assert len(data["sha256"]) == 64

def test_upload_txt():
    content = b"Hello world text content"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", file, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == ".txt"

def test_upload_csv():
    content = b"col1,col2\nval1,val2"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("data.csv", file, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == ".csv"

def test_upload_pptx():
    content = b"PK\x03\x04 pptx content"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("slides.pptx", file, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == ".pptx"

def test_upload_invalid_type():
    content = b"malicious exe content"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("bad.exe", file, "application/x-msdownload")}
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

def test_upload_empty_file():
    file = io.BytesIO(b"")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", file, "application/pdf")}
    )
    assert response.status_code == 400
    assert "Empty" in response.json()["detail"]

def test_get_document():
    content = b"test content for get"
    file = io.BytesIO(content)
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")}
    )
    doc_id = upload_response.json()["document_id"]
    get_response = client.get(f"/api/documents/{doc_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "uploaded"

def test_get_document_not_found():
    response = client.get("/api/documents/nonexistent-id")
    assert response.status_code == 404

def test_list_documents():
    #upload two documents
    for name in ["a.pdf", "b.txt"]:
        ext = name.split(".")[-1]
        content = f"content for {name}".encode()
        file = io.BytesIO(content)
        client.post("/api/documents/upload", files={"file": (name, file, f"text/{ext}")})
    response = client.get("/api/documents/")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2

def test_sha256_consistency():
    #same content should produce same hash
    content = b"consistent content for hashing"
    file1 = io.BytesIO(content)
    file2 = io.BytesIO(content)
    r1 = client.post("/api/documents/upload", files={"file": ("a.txt", file1, "text/plain")})
    r2 = client.post("/api/documents/upload", files={"file": ("b.txt", file2, "text/plain")})
    assert r1.json()["sha256"] == r2.json()["sha256"]

def test_content_stored_in_memory():
    #verify content stays in memory, not on disk
    content = b"memory only content test"
    file = io.BytesIO(content)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", file, "text/plain")}
    )
    doc_id = response.json()["document_id"]
    #check content is in memory store
    assert doc_id in _file_contents
    assert _file_contents[doc_id] == content
    assert doc_id in _documents
