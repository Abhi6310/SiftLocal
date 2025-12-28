import pytest
from app.core.llm_gate import (
    register_document_content,
    register_redaction_placeholder,
    register_from_redaction_map,
    validate_llm_payload,
    validate_text,
    clear_registry,
    get_registry_stats,
    GateResult
)
from app.services.sanitizer import detect_pii
from app.services.secret_detector import detect_secrets
from app.services.redaction import generate_redaction_map

@pytest.fixture(autouse=True)
def clean_gate():
    clear_registry()
    yield
    clear_registry()

#sample document content for testing
DOCUMENT_TEXT = """
This is a confidential internal document from Acme Corporation.
Contact our support team at support@acme.com or call 555-867-5309.
The project budget is $1.2 million and the deadline is Q4 2024.
Employee ID: EMP-12345, SSN: 123-45-6789
API Key: AKIAIOSFODNN7EXAMPLE
"""

SAFE_METADATA = {
    "page_count": 5,
    "word_count": 150,
    "file_type": "pdf",
    "has_images": True,
    "sections": ["Introduction", "Budget", "Timeline"]
}

class TestDocumentRegistration:
    def test_register_document_content(self):
        register_document_content(DOCUMENT_TEXT)
        stats = get_registry_stats()
        assert stats["document_hashes"] == 1
        assert stats["document_substrings"] > 0

    def test_register_empty_content_ignored(self):
        register_document_content("")
        register_document_content("   ")
        stats = get_registry_stats()
        assert stats["document_hashes"] == 0

    def test_register_redaction_placeholder(self):
        register_redaction_placeholder("[EMAIL_ADDRESS_1]")
        register_redaction_placeholder("[PHONE_NUMBER_1]")
        stats = get_registry_stats()
        assert stats["redaction_placeholders"] == 2

class TestPoisonPayloadRejection:
    def test_exact_document_match_rejected(self):
        register_document_content(DOCUMENT_TEXT)
        #poison payload: trying to send document text to LLM
        payload = {"messages": [{"role": "user", "content": DOCUMENT_TEXT}]}
        result = validate_llm_payload(payload)
        assert not result.allowed
        assert result.violation.violation_type == "document_hash_match"

    def test_document_substring_rejected(self):
        register_document_content(DOCUMENT_TEXT)
        #poison payload: partial document text
        payload = {
            "messages": [{
                "role": "user",
                "content": "Summarize: Contact our support team at support@acme.com or call 555-867-5309"
            }]
        }
        result = validate_llm_payload(payload)
        assert not result.allowed
        assert result.violation.violation_type == "document_substring_match"

    def test_redaction_placeholder_rejected(self):
        register_redaction_placeholder("[EMAIL_ADDRESS_1]")
        register_redaction_placeholder("[SSN_1]")
        #poison payload: redacted text leaked to LLM
        payload = {
            "prompt": "Process this: Contact [EMAIL_ADDRESS_1] for support"
        }
        result = validate_llm_payload(payload)
        assert not result.allowed
        assert result.violation.violation_type == "redaction_placeholder_detected"

    def test_generic_placeholder_pattern_rejected(self):
        #even without registering, generic placeholder patterns are suspicious
        payload = {
            "content": "The user [SECRET_KEY_5] and [PASSWORD_2] were found"
        }
        result = validate_llm_payload(payload)
        assert not result.allowed
        assert result.violation.violation_type == "redaction_placeholder_detected"

    def test_nested_payload_scanned(self):
        register_document_content(DOCUMENT_TEXT)
        #deeply nested poison attempt
        payload = {
            "request": {
                "context": {
                    "documents": [{
                        "text": "The project budget is $1.2 million and the deadline is Q4 2024"
                    }]
                }
            }
        }
        result = validate_llm_payload(payload)
        assert not result.allowed

    def test_large_freeform_text_rejected(self):
        #suspiciously large text in content field
        large_text = "a" * 3000
        payload = {"message": {"content": large_text}}
        result = validate_llm_payload(payload)
        assert not result.allowed
        assert result.violation.violation_type == "freeform_text_too_large"

class TestMetadataAllowed:
    def test_metadata_only_payload_allowed(self):
        register_document_content(DOCUMENT_TEXT)
        #safe payload: only metadata, no document text
        payload = {
            "context": SAFE_METADATA,
            "prompt": "Given a PDF with 5 pages and sections about Budget and Timeline, what questions should I ask?"
        }
        result = validate_llm_payload(payload)
        assert result.allowed

    def test_generic_prompt_allowed(self):
        register_document_content(DOCUMENT_TEXT)
        #safe: generic prompt with no document content
        payload = {
            "messages": [{
                "role": "user",
                "content": "How do I structure a project proposal?"
            }]
        }
        result = validate_llm_payload(payload)
        assert result.allowed

    def test_short_common_phrases_allowed(self):
        register_document_content("The project is ongoing")
        #common short phrases shouldnt trigger false positives
        payload = {"content": "The project looks good"}
        result = validate_llm_payload(payload)
        assert result.allowed

class TestIntegrationWithRedaction:
    def test_register_from_redaction_map(self):
        pii = detect_pii(DOCUMENT_TEXT)
        secrets = detect_secrets(DOCUMENT_TEXT)
        redaction_map = generate_redaction_map(DOCUMENT_TEXT, pii, secrets)
        register_from_redaction_map(redaction_map)
        stats = get_registry_stats()
        assert stats["document_hashes"] >= 1
        assert stats["redaction_placeholders"] > 0
        #verify redacted text cant be sent to LLM (rejected for any reason)
        result = validate_text(redaction_map.redacted_text)
        assert not result.allowed

    def test_pii_values_rejected(self):
        text = "Contact john.smith@company.com for details"
        pii = detect_pii(text)
        secrets = detect_secrets(text)
        redaction_map = generate_redaction_map(text, pii, secrets)
        register_from_redaction_map(redaction_map)
        #try to sneak email through
        payload = {"message": "Send to john.smith@company.com"}
        result = validate_llm_payload(payload)
        assert not result.allowed

class TestValidateText:
    def test_validate_text_simple(self):
        #register exact text to detect
        register_document_content("The project budget for Q4 is exactly one million dollars")
        result = validate_text("Summarize: The project budget for Q4 is exactly one million dollars")
        assert not result.allowed

    def test_validate_text_clean(self):
        register_document_content("The project budget for Q4 is exactly one million dollars")
        result = validate_text("What is a typical project budget?")
        assert result.allowed

class TestEdgeCases:
    def test_case_insensitive_matching(self):
        register_document_content("Confidential document from ACME Corporation")
        payload = {"text": "CONFIDENTIAL DOCUMENT FROM acme corporation"}
        result = validate_llm_payload(payload)
        assert not result.allowed

    def test_empty_payload_allowed(self):
        result = validate_llm_payload({})
        assert result.allowed

    def test_non_string_values_ignored(self):
        register_document_content(DOCUMENT_TEXT)
        payload = {"count": 42, "enabled": True, "items": [1, 2, 3]}
        result = validate_llm_payload(payload)
        assert result.allowed

    def test_registry_clear(self):
        register_document_content(DOCUMENT_TEXT)
        clear_registry()
        stats = get_registry_stats()
        assert stats["document_hashes"] == 0
        assert stats["document_substrings"] == 0
        #after clearing, short text that was previously registered is now allowed
        short_text = "A short test phrase for verification"
        register_document_content(short_text)
        clear_registry()
        payload = {"prompt": short_text}
        result = validate_llm_payload(payload)
        assert result.allowed
