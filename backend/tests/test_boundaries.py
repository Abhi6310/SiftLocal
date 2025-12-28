import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_database, get_connection, get_tables, DB_PATH
from app.services import memory_manager, file_handler
from app.services.memory_manager import DocumentState
from app.services.sanitizer import detect_pii
from app.services.secret_detector import detect_secrets
from app.services.redaction import generate_redaction_map

client = TestClient(app)

TEST_TEXT_WITH_PII = """
Contact john.doe@example.com for support.
Call 555-123-4567 or SSN 123-45-6789.
API key: AKIAIOSFODNN7EXAMPLE
Password: password=SuperSecret123!
"""

@pytest.fixture(autouse=True)
def clean_state():
    file_handler.clear_all()
    memory_manager.clear_all()
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    file_handler.clear_all()
    memory_manager.clear_all()
    if DB_PATH.exists():
        DB_PATH.unlink()

def test_no_document_text_in_database():
    init_database()
    conn = get_connection()
    tables = get_tables()
    for table in tables:
        cursor = conn.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            for cell in row:
                if isinstance(cell, str):
                    assert "john.doe@example.com" not in cell
                    assert "555-123-4567" not in cell
                    assert "AKIAIOSFODNN7" not in cell
    conn.close()

def test_no_redaction_map_in_database():
    init_database()
    pii = detect_pii(TEST_TEXT_WITH_PII)
    secrets = detect_secrets(TEST_TEXT_WITH_PII)
    redaction_map = generate_redaction_map(TEST_TEXT_WITH_PII, pii, secrets)
    assert len(redaction_map.entities) > 0
    assert redaction_map.original_text == TEST_TEXT_WITH_PII
    #db should remain clean even after generating redaction map in memory
    conn = get_connection()
    tables = get_tables()
    for table in tables:
        cursor = conn.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            for cell in row:
                if isinstance(cell, str):
                    assert "john.doe@example.com" not in cell
                    assert "SuperSecret123" not in cell
                    assert "[EMAIL_ADDRESS_" not in cell
                    assert "[PASSWORD_" not in cell
    conn.close()

def test_schema_contract_no_sensitive_tables():
    init_database()
    tables = get_tables()
    forbidden = {
        'documents', 'document_text', 'extracted_text',
        'redaction_maps', 'sensitive_data', 'sessions',
        'messages', 'chat_history', 'prompts', 'content'
    }
    violations = forbidden.intersection(set(tables))
    assert not violations, f"Schema violation: found forbidden tables {violations}"
    allowed = {'vault_config', 'preferences'}
    assert set(tables) == allowed, f"Unknown tables: {set(tables) - allowed}"

@pytest.mark.skip(reason="Waiting for C17 - LLM gate not yet implemented")
def test_llm_endpoint_rejects_document_text():
    pass

@pytest.mark.skip(reason="Waiting for C17-C18 - metadata extraction not yet implemented")
def test_metadata_only_allowed_in_llm_payload():
    pass

def test_upload_endpoint_no_text_in_response():
    test_content = b"This is test content with email@example.com"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", test_content, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    expected_fields = {"document_id", "filename", "file_type", "sha256", "size"}
    assert set(data.keys()) == expected_fields
    response_str = str(data)
    assert "email@example.com" not in response_str
    assert "test content" not in response_str

def test_no_endpoint_returns_raw_extract():
    test_content = b"Sensitive content with SSN 123-45-6789"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", test_content, "text/plain")}
    )
    doc_id = response.json()["document_id"]
    response = client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    response_str = str(data)
    assert "Sensitive content" not in response_str
    assert "123-45-6789" not in response_str
    expected_fields = {"document_id", "filename", "file_type", "sha256", "size", "status"}
    assert set(data.keys()) == expected_fields

def test_redaction_map_cleared_after_use():
    doc_id = "test-boundary-doc-1"
    file_handler._file_contents[doc_id] = TEST_TEXT_WITH_PII.encode()
    memory_manager.set_document_state(doc_id, DocumentState.UPLOADED)
    extract = {"text": TEST_TEXT_WITH_PII, "metadata": {"file_type": ".txt"}}
    memory_manager.store_raw_extract(doc_id, extract)
    memory_manager.transition_state(doc_id, DocumentState.PARSED)
    assert memory_manager.get_raw_extract(doc_id) is not None
    #transition to sanitized triggers cleanup per memory_manager lifecycle
    memory_manager.transition_state(doc_id, DocumentState.SANITIZED)
    assert memory_manager.get_raw_extract(doc_id) is None
    stats = memory_manager.get_memory_stats()
    assert stats["raw_extracts_count"] == 0

def test_no_global_state_leakage():
    doc_a = "doc-boundary-a"
    doc_b = "doc-boundary-b"
    text_a = "Document A with email alpha@example.com"
    text_b = "Document B with phone 999-888-7777"
    pii_a = detect_pii(text_a)
    secrets_a = detect_secrets(text_a)
    redaction_a = generate_redaction_map(text_a, pii_a, secrets_a)
    memory_manager.store_raw_extract(doc_a, {"text": text_a})
    pii_b = detect_pii(text_b)
    secrets_b = detect_secrets(text_b)
    redaction_b = generate_redaction_map(text_b, pii_b, secrets_b)
    memory_manager.store_raw_extract(doc_b, {"text": text_b})
    memory_manager.clear_raw_extract(doc_a)
    assert memory_manager.get_raw_extract(doc_a) is None
    #doc_b should be unaffected by doc_a cleanup
    extract_b = memory_manager.get_raw_extract(doc_b)
    assert extract_b is not None
    assert "999-888-7777" in extract_b["text"]
    assert "alpha@example.com" not in extract_b["text"]
    assert redaction_a.original_text != redaction_b.original_text
    assert "alpha@example.com" in redaction_a.original_text
    assert "999-888-7777" in redaction_b.original_text
