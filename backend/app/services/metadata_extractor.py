import re
from typing import Optional, List
from datetime import datetime
from app.models.metadata import (
    MetadataSchema,
    StructureInfo,
    EntitySummary,
    PDFMetadata,
    PPTXMetadata,
    CSVMetadata,
    TXTMetadata
)
from app.models.redaction import RedactionMap

def _analyze_structure(text: str) -> StructureInfo:
    #analyze text structure without retaining content
    if not text:
        return StructureInfo()
    #count paragraphs (separated by blank lines)
    paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
    paragraph_count = len(paragraphs)
    #count sentences (approximate - ends with .!?)
    sentences = re.findall(r'[^.!?]+[.!?]', text)
    sentence_count = len(sentences)
    #count words
    words = text.split()
    word_count = len(words)
    #compute averages
    avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0.0
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0.0
    return StructureInfo(
        paragraph_count=paragraph_count,
        sentence_count=sentence_count,
        word_count=word_count,
        avg_word_length=round(avg_word_length, 2),
        avg_sentence_length=round(avg_sentence_length, 2)
    )

def _summarize_entities(redaction_map: Optional[RedactionMap]) -> EntitySummary:
    #count entities by type without exposing values
    if not redaction_map or not redaction_map.entities:
        return EntitySummary()
    entity_counts: dict[str, int] = {}
    sources: dict[str, int] = {}
    for entity in redaction_map.entities:
        etype = entity.entity_type
        entity_counts[etype] = entity_counts.get(etype, 0) + 1
        sources[entity.source] = sources.get(entity.source, 0) + 1
    return EntitySummary(
        entity_counts=entity_counts,
        total_entities=len(redaction_map.entities),
        sources=sources
    )

def extract_metadata(
    document_id: str,
    raw_extract: dict,
    file_size: int,
    sha256: str,
    redaction_map: Optional[RedactionMap] = None
) -> MetadataSchema:
    #extract LLM-safe metadata from raw extract
    #returns counts, types, structure - no recoverable text
    text = raw_extract.get("text", "")
    parser_metadata = raw_extract.get("metadata", {})
    file_type = parser_metadata.get("file_type", "unknown")
    #analyze structure from text (counts only)
    structure = _analyze_structure(text)
    #summarize entities (counts only)
    entities = _summarize_entities(redaction_map)
    #build file-type specific metadata
    pdf_meta = None
    pptx_meta = None
    csv_meta = None
    txt_meta = None
    if file_type == "pdf":
        pdf_meta = PDFMetadata(
            page_count=parser_metadata.get("page_count", 0),
            char_count=parser_metadata.get("char_count", 0)
        )
    elif file_type == "pptx":
        slides = parser_metadata.get("slides", [])
        #only keep slide_number and char_count, no text
        safe_slides = [
            {"slide_number": s.get("slide_number", 0), "char_count": s.get("char_count", 0)}
            for s in slides
        ]
        pptx_meta = PPTXMetadata(
            slide_count=parser_metadata.get("slide_count", 0),
            char_count=parser_metadata.get("char_count", 0),
            slides=safe_slides
        )
    elif file_type == "csv":
        csv_meta = CSVMetadata(
            row_count=parser_metadata.get("row_count", 0),
            column_count=parser_metadata.get("column_count", 0),
            headers=parser_metadata.get("headers", []),
            char_count=parser_metadata.get("char_count", 0)
        )
    elif file_type == "txt":
        txt_meta = TXTMetadata(
            line_count=parser_metadata.get("line_count", 0),
            char_count=parser_metadata.get("char_count", 0)
        )
    return MetadataSchema(
        document_id=document_id,
        file_type=file_type,
        file_size=file_size,
        sha256=sha256,
        structure=structure,
        entities=entities,
        pdf=pdf_meta,
        pptx=pptx_meta,
        csv=csv_meta,
        txt=txt_meta,
        extracted_at=datetime.now()
    )

def validate_no_recoverable_text(metadata: MetadataSchema, original_text: str) -> bool:
    #verify metadata does not contain recoverable document text
    #returns True if safe, False if text leaked into metadata
    if not original_text or len(original_text) < 10:
        return True
    #serialize metadata to check for text leakage
    metadata_str = metadata.model_dump_json()
    #check for significant substrings (20+ chars)
    words = original_text.split()
    for i in range(len(words)):
        chunk = ' '.join(words[i:i+5])
        if len(chunk) >= 20 and chunk.lower() in metadata_str.lower():
            return False
    #check for any sentences
    sentences = re.findall(r'[^.!?]+[.!?]', original_text)
    for sentence in sentences:
        if len(sentence) >= 20 and sentence.lower().strip() in metadata_str.lower():
            return False
    return True
