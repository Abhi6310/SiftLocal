import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.memory_manager import (
    store_sanitized_content, clear_all as clear_memory,
    list_sanitized_documents
)
from app.services.review_manager import (
    list_approved_chunks, list_rejected_chunks,
    get_chunk_status, clear_all_status
)
from app.models.redaction import RedactionMap, DetectedEntity

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    clear_memory()
    clear_all_status()
    yield
    clear_memory()
    clear_all_status()

def test_review_queue_empty():
    response = client.get("/api/review/queue")
    assert response.status_code == 200
    data = response.json()
    assert data["chunks"] == []
    assert data["total_count"] == 0

def test_review_queue_with_chunks():
    #store a sanitized document
    entities = [
        DetectedEntity(
            entity_type="EMAIL_ADDRESS",
            source="pii",
            start=8,
            end=24,
            confidence=0.95,
            original_text="john@example.com",
            placeholder="[EMAIL_ADDRESS_1]"
        )
    ]
    redaction_map = RedactionMap(
        original_text="Contact john@example.com for help",
        redacted_text="Contact [EMAIL_ADDRESS_1] for help",
        entities=entities,
        created_at=datetime.now()
    )
    store_sanitized_content("doc-123", redaction_map)
    response = client.get("/api/review/queue")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["chunks"]) == 1
    chunk = data["chunks"][0]
    assert chunk["chunk_id"] == "doc-123"
    assert chunk["document_id"] == "doc-123"
    assert chunk["status"] == "pending"
    assert "[EMAIL_ADDRESS_1]" in chunk["redacted_text"]
    #original text should NOT be in response
    assert "john@example.com" not in chunk["redacted_text"]

def test_review_queue_redaction_info():
    #verify redaction metadata is exposed for highlighting
    entities = [
        DetectedEntity(
            entity_type="AWS_ACCESS_KEY",
            source="secret",
            start=10,
            end=30,
            confidence=0.9,
            original_text="AKIAIOSFODNN7EXAMPLE",
            placeholder="[AWS_ACCESS_KEY_1]"
        )
    ]
    redaction_map = RedactionMap(
        original_text="API key: AKIAIOSFODNN7EXAMPLE",
        redacted_text="API key: [AWS_ACCESS_KEY_1]",
        entities=entities,
        created_at=datetime.now()
    )
    store_sanitized_content("doc-456", redaction_map)
    response = client.get("/api/review/queue")
    chunk = response.json()["chunks"][0]
    assert len(chunk["redactions"]) == 1
    redaction = chunk["redactions"][0]
    assert redaction["placeholder"] == "[AWS_ACCESS_KEY_1]"
    assert redaction["entity_type"] == "AWS_ACCESS_KEY"
    assert redaction["source"] == "secret"
    #original_text should NOT be in redaction info
    assert "original_text" not in redaction

def test_review_queue_multiple_docs():
    #test multiple documents in queue
    for i, doc_id in enumerate(["doc-a", "doc-b", "doc-c"]):
        entities = [
            DetectedEntity(
                entity_type="PHONE_NUMBER",
                source="pii",
                start=0,
                end=12,
                confidence=0.8,
                original_text=f"555-000{i}",
                placeholder=f"[PHONE_NUMBER_1]"
            )
        ]
        redaction_map = RedactionMap(
            original_text=f"Call 555-000{i}",
            redacted_text="Call [PHONE_NUMBER_1]",
            entities=entities,
            created_at=datetime.now()
        )
        store_sanitized_content(doc_id, redaction_map)
    response = client.get("/api/review/queue")
    data = response.json()
    assert data["total_count"] == 3
    assert len(data["chunks"]) == 3

def test_review_queue_no_original_text_leak():
    #invariant test: original text must never appear in response
    original = "My SSN is 123-45-6789 and email is secret@company.com"
    redacted = "My SSN is [SSN_1] and email is [EMAIL_ADDRESS_1]"
    entities = [
        DetectedEntity(
            entity_type="US_SSN",
            source="pii",
            start=10,
            end=21,
            confidence=0.99,
            original_text="123-45-6789",
            placeholder="[SSN_1]"
        ),
        DetectedEntity(
            entity_type="EMAIL_ADDRESS",
            source="pii",
            start=36,
            end=54,
            confidence=0.95,
            original_text="secret@company.com",
            placeholder="[EMAIL_ADDRESS_1]"
        )
    ]
    redaction_map = RedactionMap(
        original_text=original,
        redacted_text=redacted,
        entities=entities,
        created_at=datetime.now()
    )
    store_sanitized_content("doc-pii", redaction_map)
    response = client.get("/api/review/queue")
    response_text = response.text
    #none of the original sensitive data should appear
    assert "123-45-6789" not in response_text
    assert "secret@company.com" not in response_text
    #placeholders should be present
    assert "[SSN_1]" in response_text
    assert "[EMAIL_ADDRESS_1]" in response_text

def _create_test_chunk(doc_id):
    entities = [
        DetectedEntity(
            entity_type="EMAIL_ADDRESS",
            source="pii",
            start=0,
            end=16,
            confidence=0.95,
            original_text="test@example.com",
            placeholder="[EMAIL_ADDRESS_1]"
        )
    ]
    redaction_map = RedactionMap(
        original_text="test@example.com content",
        redacted_text="[EMAIL_ADDRESS_1] content",
        entities=entities,
        created_at=datetime.now()
    )
    store_sanitized_content(doc_id, redaction_map)

def test_approve_chunk():
    _create_test_chunk("doc-approve-1")
    #initially pending
    response = client.get("/api/review/queue")
    chunk = response.json()["chunks"][0]
    assert chunk["status"] == "pending"
    #approve
    response = client.post("/api/review/doc-approve-1/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "approved"
    #verify status updated
    response = client.get("/api/review/queue")
    chunk = response.json()["chunks"][0]
    assert chunk["status"] == "approved"
    #verify in approved list
    assert "doc-approve-1" in list_approved_chunks()

def test_reject_chunk():
    _create_test_chunk("doc-reject-1")
    #reject
    response = client.post("/api/review/doc-reject-1/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "rejected"
    #verify status updated
    response = client.get("/api/review/queue")
    chunk = response.json()["chunks"][0]
    assert chunk["status"] == "rejected"
    #verify in rejected list, not in approved
    assert "doc-reject-1" in list_rejected_chunks()
    assert "doc-reject-1" not in list_approved_chunks()

def test_approve_nonexistent_chunk():
    response = client.post("/api/review/nonexistent/approve")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_reject_nonexistent_chunk():
    response = client.post("/api/review/nonexistent/reject")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_bulk_approve():
    for i in range(3):
        _create_test_chunk(f"bulk-approve-{i}")
    response = client.post(
        "/api/review/bulk/approve",
        json={"chunk_ids": ["bulk-approve-0", "bulk-approve-1", "bulk-approve-2"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    #all should be approved
    approved = list_approved_chunks()
    assert "bulk-approve-0" in approved
    assert "bulk-approve-1" in approved
    assert "bulk-approve-2" in approved

def test_bulk_reject():
    for i in range(3):
        _create_test_chunk(f"bulk-reject-{i}")
    response = client.post(
        "/api/review/bulk/reject",
        json={"chunk_ids": ["bulk-reject-0", "bulk-reject-1", "bulk-reject-2"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    #all should be rejected
    rejected = list_rejected_chunks()
    assert "bulk-reject-0" in rejected
    assert "bulk-reject-1" in rejected
    assert "bulk-reject-2" in rejected
    #none should be approved
    assert len(list_approved_chunks()) == 0

def test_bulk_approve_partial():
    #only some chunks exist
    _create_test_chunk("partial-0")
    _create_test_chunk("partial-1")
    response = client.post(
        "/api/review/bulk/approve",
        json={"chunk_ids": ["partial-0", "partial-1", "nonexistent"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 2
    assert data["failure_count"] == 1

def test_rejected_excluded_from_approved():
    #create and reject a chunk
    _create_test_chunk("excluded-1")
    client.post("/api/review/excluded-1/reject")
    #verify excluded from approved list (for C21 eligibility)
    assert "excluded-1" not in list_approved_chunks()
    assert "excluded-1" in list_rejected_chunks()
    #create and approve another
    _create_test_chunk("included-1")
    client.post("/api/review/included-1/approve")
    #verify approved is included
    assert "included-1" in list_approved_chunks()
    assert "included-1" not in list_rejected_chunks()

def test_status_counts():
    _create_test_chunk("count-pending")
    _create_test_chunk("count-approved")
    _create_test_chunk("count-rejected")
    client.post("/api/review/count-approved/approve")
    client.post("/api/review/count-rejected/reject")
    response = client.get("/api/review/counts")
    assert response.status_code == 200
    counts = response.json()
    assert counts["pending"] == 1
    assert counts["approved"] == 1
    assert counts["rejected"] == 1

def test_approval_state_in_memory_only():
    #I4 invariant: approval state must not persist to DB
    _create_test_chunk("memory-test")
    client.post("/api/review/memory-test/approve")
    assert get_chunk_status("memory-test") == "approved"
    #clear memory clears status
    clear_memory()
    #no sanitized content = no status tracking possible
    assert list_sanitized_documents() == []
