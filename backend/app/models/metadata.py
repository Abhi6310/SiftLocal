from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class StructureInfo(BaseModel):
    #structure information without text content
    paragraph_count: int = 0
    sentence_count: int = 0
    word_count: int = 0
    avg_word_length: float = 0.0
    avg_sentence_length: float = 0.0

class EntitySummary(BaseModel):
    #count of detected entities by type (no values)
    entity_counts: Dict[str, int] = {}
    total_entities: int = 0
    sources: Dict[str, int] = {}  #pii vs secret counts

class PDFMetadata(BaseModel):
    page_count: int
    char_count: int

class PPTXMetadata(BaseModel):
    slide_count: int
    char_count: int
    slides: List[Dict[str, int]] = []  #slide_number, char_count only

class CSVMetadata(BaseModel):
    row_count: int
    column_count: int
    headers: List[str] = []  #column headers are typically safe
    char_count: int

class TXTMetadata(BaseModel):
    line_count: int
    char_count: int

class MetadataSchema(BaseModel):
    document_id: str
    file_type: str
    file_size: int
    sha256: str
    #structural analysis
    structure: StructureInfo
    #entity summary (counts only, no values)
    entities: EntitySummary
    #file-type specific metadata
    pdf: Optional[PDFMetadata] = None
    pptx: Optional[PPTXMetadata] = None
    csv: Optional[CSVMetadata] = None
    txt: Optional[TXTMetadata] = None
    #timestamp
    extracted_at: datetime
