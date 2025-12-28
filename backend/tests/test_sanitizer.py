import pytest
from app.services.sanitizer import detect_pii, get_analyzer, PIIEntity

def test_detect_email():
    text = "Contact me at john.doe@example.com"
    entities = detect_pii(text)
    assert len(entities) >= 1
    email_entities = [e for e in entities if e.entity_type == "EMAIL_ADDRESS"]
    assert len(email_entities) == 1
    assert email_entities[0].text == "john.doe@example.com"

def test_detect_phone():
    #presidio needs score threshold consideration; phone patterns score 0.4
    text = "Call me at 555-123-4567"
    entities = detect_pii(text, score_threshold=0.3)
    phone_entities = [e for e in entities if e.entity_type == "PHONE_NUMBER"]
    assert len(phone_entities) >= 1

def test_detect_ssn():
    #SSN: prefix provides context for higher confidence detection
    text = "SSN: 219-09-9999"
    entities = detect_pii(text)
    ssn_entities = [e for e in entities if e.entity_type == "US_SSN"]
    assert len(ssn_entities) == 1
    assert "219-09-9999" in ssn_entities[0].text

def test_detect_multiple_entities():
    text = "John Doe (john@example.com) lives at 123 Main St, SSN: 219-09-9999"
    entities = detect_pii(text)
    entity_types = {e.entity_type for e in entities}
    #should detect email, SSN, and person/location from spaCy
    assert "EMAIL_ADDRESS" in entity_types
    assert "US_SSN" in entity_types
    assert len(entities) >= 2

def test_no_false_positives():
    text = "The quick brown fox jumps over the lazy dog"
    entities = detect_pii(text)
    #may detect some entities but shouldn't detect PII types
    pii_types = {"EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"}
    detected_pii = [e for e in entities if e.entity_type in pii_types]
    assert len(detected_pii) == 0

def test_analyzer_singleton():
    analyzer1 = get_analyzer()
    analyzer2 = get_analyzer()
    assert analyzer1 is analyzer2
