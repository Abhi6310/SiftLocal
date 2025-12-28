import pytest
from app.services.sanitizer import PIIEntity
from app.services.secret_detector import SecretEntity
from app.services.redaction import (
    merge_entities, generate_placeholders, apply_redaction,
    reverse_redaction, generate_redaction_map
)
from app.models.redaction import DetectedEntity

def test_merge_entities_no_overlap():
    pii = [PIIEntity(entity_type="EMAIL_ADDRESS", start=10, end=30, score=0.95, text="john@example.com")]
    secrets = [SecretEntity(secret_type="GENERIC_API_KEY", start=50, end=70, confidence=0.7, text="abc123secret")]
    merged = merge_entities(pii, secrets)
    assert len(merged) == 2
    assert merged[0].entity_type == "EMAIL_ADDRESS"
    assert merged[1].entity_type == "GENERIC_API_KEY"

def test_merge_entities_with_overlap():
    #overlapping entities, higher confidence wins
    pii = [PIIEntity(entity_type="EMAIL_ADDRESS", start=10, end=30, score=0.95, text="john@example.com")]
    secrets = [SecretEntity(secret_type="GENERIC_API_KEY", start=15, end=35, confidence=0.7, text="somesecret")]
    merged = merge_entities(pii, secrets)
    assert len(merged) == 1
    assert merged[0].entity_type == "EMAIL_ADDRESS"
    assert merged[0].confidence == 0.95

def test_generate_redaction_map():
    text = "Contact john@example.com, API key: sk_live_abc123"
    pii = [PIIEntity(entity_type="EMAIL_ADDRESS", start=8, end=24, score=0.95, text="john@example.com")]
    secrets = [SecretEntity(secret_type="STRIPE_SECRET_KEY", start=35, end=49, confidence=0.9, text="sk_live_abc123")]
    rmap = generate_redaction_map(text, pii, secrets)
    assert "[EMAIL_ADDRESS_1]" in rmap.redacted_text
    assert "[STRIPE_SECRET_KEY_1]" in rmap.redacted_text
    assert "john@example.com" not in rmap.redacted_text
    assert len(rmap.entities) == 2

def test_placeholder_format():
    entities = [DetectedEntity(
        entity_type="EMAIL_ADDRESS", source="pii", start=0, end=10,
        confidence=0.9, original_text="test@test.com", placeholder=""
    )]
    result = generate_placeholders(entities)
    assert result[0].placeholder == "[EMAIL_ADDRESS_1]"

def test_sequential_placeholders():
    entities = [
        DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=0, end=10, confidence=0.9, original_text="a@a.com", placeholder=""),
        DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=20, end=30, confidence=0.9, original_text="b@b.com", placeholder=""),
        DetectedEntity(entity_type="PHONE_NUMBER", source="pii", start=40, end=50, confidence=0.9, original_text="555-1234", placeholder="")
    ]
    result = generate_placeholders(entities)
    assert result[0].placeholder == "[EMAIL_ADDRESS_1]"
    assert result[1].placeholder == "[EMAIL_ADDRESS_2]"
    assert result[2].placeholder == "[PHONE_NUMBER_1]"

def test_apply_redaction():
    text = "Email: john@example.com end"
    entities = [DetectedEntity(
        entity_type="EMAIL_ADDRESS", source="pii", start=7, end=23,
        confidence=0.9, original_text="john@example.com", placeholder="[EMAIL_ADDRESS_1]"
    )]
    result = apply_redaction(text, entities)
    assert result == "Email: [EMAIL_ADDRESS_1] end"

def test_reverse_redaction():
    redacted = "Email: [EMAIL_ADDRESS_1] end"
    entities = [DetectedEntity(
        entity_type="EMAIL_ADDRESS", source="pii", start=7, end=23,
        confidence=0.9, original_text="john@example.com", placeholder="[EMAIL_ADDRESS_1]"
    )]
    result = reverse_redaction(redacted, entities)
    assert result == "Email: john@example.com end"

def test_empty_entities():
    text = "No sensitive data here"
    pii = []
    secrets = []
    rmap = generate_redaction_map(text, pii, secrets)
    assert rmap.redacted_text == text
    assert len(rmap.entities) == 0

def test_adjacent_entities():
    #adjacent (not overlapping) entities should both be kept
    pii = [
        PIIEntity(entity_type="EMAIL_ADDRESS", start=0, end=10, score=0.9, text="a@test.com"),
        PIIEntity(entity_type="PHONE_NUMBER", start=10, end=20, score=0.8, text="555-1234")
    ]
    merged = merge_entities(pii, [])
    assert len(merged) == 2

def test_offset_accuracy():
    text = "AAA john@example.com BBB secret123 CCC"
    pii = [PIIEntity(entity_type="EMAIL_ADDRESS", start=4, end=20, score=0.9, text="john@example.com")]
    secrets = [SecretEntity(secret_type="GENERIC_API_KEY", start=25, end=34, confidence=0.7, text="secret123")]
    rmap = generate_redaction_map(text, pii, secrets)
    #verify original text can be reconstructed
    restored = reverse_redaction(rmap.redacted_text, rmap.entities)
    assert restored == text
