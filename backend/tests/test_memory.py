import pytest
from app.services import memory_manager, file_handler
from app.services.memory_manager import DocumentState

@pytest.fixture(autouse=True)
def clean_state():
    file_handler.clear_all()
    memory_manager.clear_all()
    yield
    file_handler.clear_all()
    memory_manager.clear_all()

def test_raw_extract_lifecycle():
    #simulate full lifecycle: upload -> parse -> sanitize
    doc_id = "test-doc-1"
    file_content = b"test file content"
    extract = {"text": "parsed content", "metadata": {"pages": 1}}
    #step 1: simulate upload - file bytes stored
    file_handler._file_contents[doc_id] = file_content
    memory_manager.set_document_state(doc_id, DocumentState.UPLOADED)
    assert file_handler.get_file_content(doc_id) == file_content
    #step 2: transition to PARSED - file bytes should be cleared
    memory_manager.store_raw_extract(doc_id, extract)
    memory_manager.transition_state(doc_id, DocumentState.PARSED)
    assert file_handler.get_file_content(doc_id) is None
    assert memory_manager.get_raw_extract(doc_id) == extract
    #step 3: transition to SANITIZED - raw extract should be cleared
    memory_manager.transition_state(doc_id, DocumentState.SANITIZED)
    assert memory_manager.get_raw_extract(doc_id) is None
    #I4 proven: no raw extract remains after sanitization

def test_state_transitions():
    doc_id = "test-doc-2"
    #verify state machine transitions
    states = [
        DocumentState.UPLOADED,
        DocumentState.PARSING,
        DocumentState.PARSED,
        DocumentState.SANITIZING,
        DocumentState.SANITIZED,
        DocumentState.COMPLETED
    ]
    for state in states:
        memory_manager.transition_state(doc_id, state)
        assert memory_manager.get_document_state(doc_id) == state

def test_memory_isolation():
    doc_a = "doc-a"
    doc_b = "doc-b"
    extract_a = {"text": "content a"}
    extract_b = {"text": "content b"}
    #store both
    memory_manager.store_raw_extract(doc_a, extract_a)
    memory_manager.store_raw_extract(doc_b, extract_b)
    #clear doc_a
    memory_manager.clear_raw_extract(doc_a)
    #verify isolation: doc_b unaffected
    assert memory_manager.get_raw_extract(doc_a) is None
    assert memory_manager.get_raw_extract(doc_b) == extract_b

def test_cleanup_document():
    doc_id = "test-doc-3"
    #setup: simulate upload and parse
    file_handler._file_contents[doc_id] = b"file bytes"
    memory_manager.store_raw_extract(doc_id, {"text": "parsed"})
    memory_manager.set_document_state(doc_id, DocumentState.PARSED)
    #verify everything is stored
    assert file_handler.get_file_content(doc_id) is not None
    assert memory_manager.get_raw_extract(doc_id) is not None
    assert memory_manager.get_document_state(doc_id) is not None
    #cleanup
    memory_manager.cleanup_document(doc_id)
    #verify all memory cleared
    assert file_handler.get_file_content(doc_id) is None
    assert memory_manager.get_raw_extract(doc_id) is None
    assert memory_manager.get_document_state(doc_id) is None

def test_no_persistence_after_error():
    doc_id = "test-doc-4"
    #simulate upload
    file_handler._file_contents[doc_id] = b"file bytes"
    memory_manager.store_raw_extract(doc_id, {"text": "parsed"})
    memory_manager.set_document_state(doc_id, DocumentState.PARSING)
    #simulate error during processing
    memory_manager.transition_state(doc_id, DocumentState.ERROR)
    #cleanup should still work
    memory_manager.cleanup_document(doc_id)
    #verify no leaked memory
    assert file_handler.get_file_content(doc_id) is None
    assert memory_manager.get_raw_extract(doc_id) is None
    assert memory_manager.get_document_state(doc_id) is None

def test_memory_stats():
    #verify stats reporting is accurate
    stats = memory_manager.get_memory_stats()
    assert stats["file_contents_count"] == 0
    assert stats["raw_extracts_count"] == 0
    assert stats["document_states_count"] == 0
    #add some data
    file_handler._file_contents["doc1"] = b"content1"
    file_handler._file_contents["doc2"] = b"content2"
    memory_manager.store_raw_extract("doc1", {"text": "a"})
    memory_manager.set_document_state("doc1", DocumentState.UPLOADED)
    memory_manager.set_document_state("doc2", DocumentState.PARSING)
    #verify counts
    stats = memory_manager.get_memory_stats()
    assert stats["file_contents_count"] == 2
    assert stats["raw_extracts_count"] == 1
    assert stats["document_states_count"] == 2
