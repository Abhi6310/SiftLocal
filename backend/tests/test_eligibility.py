import pytest
from datetime import datetime
from app.services import injection_eligibility, memory_manager, review_manager
from app.services.injection_eligibility import InjectionNotEligibleError
from app.models.redaction import RedactionMap, DetectedEntity

@pytest.fixture(autouse=True)
def cleanup():
    memory_manager.clear_all()
    yield
    memory_manager.clear_all()

def _create_test_chunk(chunk_id: str) -> RedactionMap:
    #helper to create a test chunk in sanitized content
    entity = DetectedEntity(
        entity_type="EMAIL",
        source="pii",
        start=18,
        end=34,
        confidence=0.95,
        original_text="john@example.com",
        placeholder="[EMAIL_1]"
    )
    redaction_map = RedactionMap(
        original_text="Test content with john@example.com",
        redacted_text="Test content with [EMAIL_1]",
        entities=[entity],
        created_at=datetime.now()
    )
    memory_manager.store_sanitized_content(chunk_id, redaction_map)
    return redaction_map

def test_approved_chunk_is_eligible():
    #approved chunks should be eligible for injection
    chunk_id = "doc-001"
    _create_test_chunk(chunk_id)
    review_manager.approve_chunk(chunk_id)
    assert injection_eligibility.is_eligible(chunk_id) is True

def test_pending_chunk_is_not_eligible():
    #pending chunks should NOT be eligible for injection
    chunk_id = "doc-002"
    _create_test_chunk(chunk_id)
    #default status is pending
    assert injection_eligibility.is_eligible(chunk_id) is False

def test_rejected_chunk_is_not_eligible():
    #rejected chunks should NOT be eligible for injection
    chunk_id = "doc-003"
    _create_test_chunk(chunk_id)
    review_manager.reject_chunk(chunk_id)
    assert injection_eligibility.is_eligible(chunk_id) is False

def test_nonexistent_chunk_is_not_eligible():
    #chunks that don't exist should not be eligible
    assert injection_eligibility.is_eligible("nonexistent-id") is False

def test_require_eligible_raises_for_pending():
    #require_eligible should raise for pending chunks
    chunk_id = "doc-004"
    _create_test_chunk(chunk_id)
    with pytest.raises(InjectionNotEligibleError) as exc_info:
        injection_eligibility.require_eligible(chunk_id)
    assert "pending review" in str(exc_info.value)
    assert exc_info.value.chunk_id == chunk_id

def test_require_eligible_raises_for_rejected():
    #require_eligible should raise for rejected chunks
    chunk_id = "doc-005"
    _create_test_chunk(chunk_id)
    review_manager.reject_chunk(chunk_id)
    with pytest.raises(InjectionNotEligibleError) as exc_info:
        injection_eligibility.require_eligible(chunk_id)
    assert "rejected" in str(exc_info.value)

def test_require_eligible_raises_for_nonexistent():
    #require_eligible should raise for nonexistent chunks
    with pytest.raises(InjectionNotEligibleError) as exc_info:
        injection_eligibility.require_eligible("ghost-chunk")
    assert "does not exist" in str(exc_info.value)

def test_require_eligible_passes_for_approved():
    #require_eligible should pass for approved chunks
    chunk_id = "doc-006"
    _create_test_chunk(chunk_id)
    review_manager.approve_chunk(chunk_id)
    #should not raise
    injection_eligibility.require_eligible(chunk_id)

def test_get_eligible_content_returns_approved_content():
    #get_eligible_content should return content for approved chunks
    chunk_id = "doc-007"
    redaction_map = _create_test_chunk(chunk_id)
    review_manager.approve_chunk(chunk_id)
    content = injection_eligibility.get_eligible_content(chunk_id)
    assert content == redaction_map

def test_get_eligible_content_raises_for_pending():
    #get_eligible_content should raise for pending chunks
    chunk_id = "doc-008"
    _create_test_chunk(chunk_id)
    with pytest.raises(InjectionNotEligibleError):
        injection_eligibility.get_eligible_content(chunk_id)

def test_get_all_eligible_returns_only_approved():
    #get_all_eligible should return only approved chunk ids
    _create_test_chunk("chunk-a")
    _create_test_chunk("chunk-b")
    _create_test_chunk("chunk-c")
    review_manager.approve_chunk("chunk-a")
    review_manager.reject_chunk("chunk-b")
    #chunk-c remains pending
    eligible = injection_eligibility.get_all_eligible()
    assert "chunk-a" in eligible
    assert "chunk-b" not in eligible
    assert "chunk-c" not in eligible

def test_get_eligible_contents_returns_approved_map():
    #get_eligible_contents should return content dict for all approved chunks
    map_a = _create_test_chunk("chunk-x")
    _create_test_chunk("chunk-y")
    review_manager.approve_chunk("chunk-x")
    #chunk-y remains pending
    contents = injection_eligibility.get_eligible_contents()
    assert "chunk-x" in contents
    assert contents["chunk-x"] == map_a
    assert "chunk-y" not in contents

def test_eligibility_summary():
    #get_eligibility_summary should return accurate counts
    _create_test_chunk("s-1")
    _create_test_chunk("s-2")
    _create_test_chunk("s-3")
    _create_test_chunk("s-4")
    review_manager.approve_chunk("s-1")
    review_manager.approve_chunk("s-2")
    review_manager.reject_chunk("s-3")
    #s-4 remains pending
    summary = injection_eligibility.get_eligibility_summary()
    assert summary["eligible_count"] == 2
    assert summary["pending_count"] == 1
    assert summary["rejected_count"] == 1
    assert "s-1" in summary["eligible_ids"]
    assert "s-2" in summary["eligible_ids"]

def test_unapproved_chunk_cannot_be_injected():
    #critical invariant: unapproved chunks must never be injectable
    chunk_id = "sensitive-doc"
    _create_test_chunk(chunk_id)
    #try to get content without approval - should fail
    with pytest.raises(InjectionNotEligibleError):
        injection_eligibility.get_eligible_content(chunk_id)
    #approve it
    review_manager.approve_chunk(chunk_id)
    #now it should work
    content = injection_eligibility.get_eligible_content(chunk_id)
    assert content is not None
