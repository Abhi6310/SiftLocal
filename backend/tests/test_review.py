import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.memory_manager import (
    store_sanitized_content, clear_all as clear_memory,
    list_sanitized_documents
)
from app.models.redaction import RedactionMap, DetectedEntity

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    clear_memory()
    yield
    clear_memory()

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
