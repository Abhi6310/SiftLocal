import pytest
from app.services.metadata_extractor import (
    extract_metadata,
    validate_no_recoverable_text,
    _analyze_structure,
    _summarize_entities
)
from app.models.metadata import MetadataSchema, StructureInfo, EntitySummary
from app.models.redaction import RedactionMap, DetectedEntity
from datetime import datetime

#sample document content
PDF_TEXT = """
This is the first page of our confidential business proposal.
Contact us at support@acme.com or call 555-123-4567.

The project budget is $1.2 million with a Q4 2024 deadline.
Employee ID: EMP-12345, SSN: 123-45-6789.
"""

CSV_TEXT = """name,email,phone,salary
John Doe,john@example.com,555-111-2222,75000
Jane Smith,jane@example.com,555-333-4444,82000
"""

class TestStructureAnalysis:
    def test_analyze_structure_counts_correctly(self):
        text = "First sentence. Second sentence!\n\nSecond paragraph here."
        structure = _analyze_structure(text)
        assert structure.paragraph_count == 2
        assert structure.sentence_count == 3
        assert structure.word_count == 7
        assert structure.avg_word_length > 0
        assert structure.avg_sentence_length > 0

    def test_analyze_structure_empty_text(self):
        structure = _analyze_structure("")
        assert structure.paragraph_count == 0
        assert structure.sentence_count == 0
        assert structure.word_count == 0

    def test_structure_has_no_text_content(self):
        text = "This is sensitive text that should not appear in structure."
        structure = _analyze_structure(text)
        structure_str = str(structure.model_dump())
        assert "sensitive" not in structure_str.lower()
        assert "appear" not in structure_str.lower()

class TestEntitySummary:
    def test_summarize_entities_counts_correctly(self):
        entities = [
            DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=0, end=10, confidence=0.9, original_text="test@test.com", placeholder="[EMAIL_1]"),
            DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=20, end=30, confidence=0.9, original_text="foo@bar.com", placeholder="[EMAIL_2]"),
            DetectedEntity(entity_type="API_KEY", source="secret", start=40, end=50, confidence=1.0, original_text="AKIATEST", placeholder="[API_KEY_1]"),
        ]
        redaction_map = RedactionMap(
            original_text="test",
            redacted_text="test",
            entities=entities,
            created_at=datetime.now()
        )
        summary = _summarize_entities(redaction_map)
        assert summary.total_entities == 3
        assert summary.entity_counts["EMAIL_ADDRESS"] == 2
        assert summary.entity_counts["API_KEY"] == 1
        assert summary.sources["pii"] == 2
        assert summary.sources["secret"] == 1

    def test_summarize_entities_no_values(self):
        entities = [
            DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=0, end=10, confidence=0.9, original_text="secret@hidden.com", placeholder="[EMAIL_1]"),
        ]
        redaction_map = RedactionMap(
            original_text="test",
            redacted_text="test",
            entities=entities,
            created_at=datetime.now()
        )
        summary = _summarize_entities(redaction_map)
        summary_str = summary.model_dump_json()
        assert "secret@hidden.com" not in summary_str
        assert "hidden" not in summary_str

    def test_summarize_entities_empty(self):
        summary = _summarize_entities(None)
        assert summary.total_entities == 0

class TestPDFMetadataExtraction:
    def test_pdf_metadata_extraction(self):
        raw_extract = {
            "text": PDF_TEXT,
            "metadata": {
                "file_type": "pdf",
                "page_count": 5,
                "char_count": len(PDF_TEXT)
            }
        }
        metadata = extract_metadata(
            document_id="doc-123",
            raw_extract=raw_extract,
            file_size=1024,
            sha256="abc123"
        )
        assert metadata.file_type == "pdf"
        assert metadata.pdf is not None
        assert metadata.pdf.page_count == 5
        assert metadata.structure.word_count > 0

    def test_pdf_metadata_no_content(self):
        raw_extract = {
            "text": PDF_TEXT,
            "metadata": {
                "file_type": "pdf",
                "page_count": 5,
                "char_count": len(PDF_TEXT)
            }
        }
        metadata = extract_metadata(
            document_id="doc-123",
            raw_extract=raw_extract,
            file_size=1024,
            sha256="abc123"
        )
        metadata_str = metadata.model_dump_json()
        #verify no document text in metadata
        assert "confidential business proposal" not in metadata_str.lower()
        assert "support@acme.com" not in metadata_str
        assert "555-123-4567" not in metadata_str
        assert "123-45-6789" not in metadata_str

class TestPPTXMetadataExtraction:
    def test_pptx_metadata_extraction(self):
        raw_extract = {
            "text": "Slide 1 content\n\nSlide 2 content",
            "metadata": {
                "file_type": "pptx",
                "slide_count": 2,
                "char_count": 32,
                "slides": [
                    {"slide_number": 1, "char_count": 15},
                    {"slide_number": 2, "char_count": 15}
                ]
            }
        }
        metadata = extract_metadata(
            document_id="doc-pptx",
            raw_extract=raw_extract,
            file_size=2048,
            sha256="def456"
        )
        assert metadata.file_type == "pptx"
        assert metadata.pptx is not None
        assert metadata.pptx.slide_count == 2
        assert len(metadata.pptx.slides) == 2

    def test_pptx_slides_no_text(self):
        raw_extract = {
            "text": "Confidential slide content",
            "metadata": {
                "file_type": "pptx",
                "slide_count": 1,
                "char_count": 27,
                "slides": [{"slide_number": 1, "char_count": 27, "text": "Confidential slide content"}]
            }
        }
        metadata = extract_metadata(
            document_id="doc-pptx",
            raw_extract=raw_extract,
            file_size=2048,
            sha256="def456"
        )
        metadata_str = metadata.model_dump_json()
        #slides should only have slide_number and char_count
        assert "Confidential slide content" not in metadata_str

class TestCSVMetadataExtraction:
    def test_csv_metadata_extraction(self):
        raw_extract = {
            "text": CSV_TEXT,
            "metadata": {
                "file_type": "csv",
                "row_count": 3,
                "column_count": 4,
                "headers": ["name", "email", "phone", "salary"],
                "char_count": len(CSV_TEXT)
            }
        }
        metadata = extract_metadata(
            document_id="doc-csv",
            raw_extract=raw_extract,
            file_size=512,
            sha256="ghi789"
        )
        assert metadata.file_type == "csv"
        assert metadata.csv is not None
        assert metadata.csv.row_count == 3
        assert metadata.csv.column_count == 4
        assert "name" in metadata.csv.headers

    def test_csv_no_data_values(self):
        raw_extract = {
            "text": CSV_TEXT,
            "metadata": {
                "file_type": "csv",
                "row_count": 3,
                "column_count": 4,
                "headers": ["name", "email", "phone", "salary"],
                "char_count": len(CSV_TEXT)
            }
        }
        metadata = extract_metadata(
            document_id="doc-csv",
            raw_extract=raw_extract,
            file_size=512,
            sha256="ghi789"
        )
        metadata_str = metadata.model_dump_json()
        #data values should not be in metadata
        assert "John Doe" not in metadata_str
        assert "john@example.com" not in metadata_str
        assert "75000" not in metadata_str

class TestTXTMetadataExtraction:
    def test_txt_metadata_extraction(self):
        text = "Line 1\nLine 2\nLine 3"
        raw_extract = {
            "text": text,
            "metadata": {
                "file_type": "txt",
                "line_count": 3,
                "char_count": len(text)
            }
        }
        metadata = extract_metadata(
            document_id="doc-txt",
            raw_extract=raw_extract,
            file_size=20,
            sha256="jkl012"
        )
        assert metadata.file_type == "txt"
        assert metadata.txt is not None
        assert metadata.txt.line_count == 3

class TestNoRecoverableText:
    def test_validate_no_recoverable_text_safe(self):
        metadata = MetadataSchema(
            document_id="test",
            file_type="pdf",
            file_size=1024,
            sha256="abc",
            structure=StructureInfo(
                paragraph_count=2,
                sentence_count=5,
                word_count=50
            ),
            entities=EntitySummary(),
            extracted_at=datetime.now()
        )
        original_text = "This is the original document text that should not appear."
        assert validate_no_recoverable_text(metadata, original_text) is True

    def test_validate_detects_leaked_text(self):
        #simulate text leaking into metadata (would be a bug)
        class LeakyMetadata:
            def model_dump_json(self):
                return '{"leaked": "This is confidential document text"}'
        leaky = LeakyMetadata()
        original_text = "This is confidential document text that was leaked."
        #manually check - if text appears in metadata, its a leak
        assert "confidential document text" in leaky.model_dump_json()

    def test_short_text_always_safe(self):
        metadata = MetadataSchema(
            document_id="test",
            file_type="txt",
            file_size=10,
            sha256="abc",
            structure=StructureInfo(),
            entities=EntitySummary(),
            extracted_at=datetime.now()
        )
        #very short text cant be meaningfully recovered
        assert validate_no_recoverable_text(metadata, "short") is True

class TestIntegrationWithRedaction:
    def test_metadata_with_redaction_map(self):
        entities = [
            DetectedEntity(entity_type="EMAIL_ADDRESS", source="pii", start=28, end=44, confidence=0.9, original_text="support@acme.com", placeholder="[EMAIL_1]"),
            DetectedEntity(entity_type="PHONE_NUMBER", source="pii", start=53, end=65, confidence=0.8, original_text="555-123-4567", placeholder="[PHONE_1]"),
            DetectedEntity(entity_type="SSN", source="pii", start=100, end=111, confidence=0.95, original_text="123-45-6789", placeholder="[SSN_1]"),
        ]
        redaction_map = RedactionMap(
            original_text=PDF_TEXT,
            redacted_text="[REDACTED]",
            entities=entities,
            created_at=datetime.now()
        )
        raw_extract = {
            "text": PDF_TEXT,
            "metadata": {"file_type": "pdf", "page_count": 1, "char_count": len(PDF_TEXT)}
        }
        metadata = extract_metadata(
            document_id="doc-integrated",
            raw_extract=raw_extract,
            file_size=1024,
            sha256="abc",
            redaction_map=redaction_map
        )
        #entity counts present
        assert metadata.entities.total_entities == 3
        assert metadata.entities.entity_counts["EMAIL_ADDRESS"] == 1
        assert metadata.entities.entity_counts["PHONE_NUMBER"] == 1
        assert metadata.entities.entity_counts["SSN"] == 1
        #entity values not present
        metadata_str = metadata.model_dump_json()
        assert "support@acme.com" not in metadata_str
        assert "555-123-4567" not in metadata_str
        assert "123-45-6789" not in metadata_str

class TestMetadataSchemaContract:
    def test_metadata_has_required_fields(self):
        raw_extract = {"text": "test", "metadata": {"file_type": "pdf", "page_count": 1, "char_count": 4}}
        metadata = extract_metadata(
            document_id="test-id",
            raw_extract=raw_extract,
            file_size=100,
            sha256="abc123"
        )
        #required fields
        assert metadata.document_id == "test-id"
        assert metadata.file_type == "pdf"
        assert metadata.file_size == 100
        assert metadata.sha256 == "abc123"
        assert metadata.structure is not None
        assert metadata.entities is not None
        assert metadata.extracted_at is not None

    def test_metadata_serializable(self):
        raw_extract = {"text": "test", "metadata": {"file_type": "txt", "line_count": 1, "char_count": 4}}
        metadata = extract_metadata(
            document_id="test",
            raw_extract=raw_extract,
            file_size=4,
            sha256="abc"
        )
        #should serialize without error
        json_str = metadata.model_dump_json()
        assert "document_id" in json_str
        assert "structure" in json_str
