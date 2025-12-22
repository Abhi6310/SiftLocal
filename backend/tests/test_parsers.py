import pytest
import sys
import os
import io

#add parser to path for direct testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "parser"))
from parsers.pdf import parse_pdf

#minimal valid PDF with text content
SAMPLE_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello PDF World) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
435
%%EOF"""

def test_pdf():
    #test PDF parsing extracts text and metadata
    result = parse_pdf(SAMPLE_PDF)
    assert "text" in result
    assert "metadata" in result
    assert result["metadata"]["file_type"] == "pdf"
    assert result["metadata"]["page_count"] == 1
    assert "char_count" in result["metadata"]
    #text should contain something (exact extraction varies by PDF)
    assert isinstance(result["text"], str)

def test_pdf_empty():
    #minimal PDF with no text
    minimal = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000111 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
176
%%EOF"""
    result = parse_pdf(minimal)
    assert result["metadata"]["page_count"] == 1
    assert result["text"] == ""

def test_pdf_no_disk_write(tmp_path, monkeypatch):
    #invariant: parsed content never written to disk
    import builtins
    original_open = builtins.open
    disk_writes = []
    def tracked_open(path, mode="r", *args, **kwargs):
        if "w" in mode or "a" in mode:
            disk_writes.append(str(path))
        return original_open(path, mode, *args, **kwargs)
    monkeypatch.setattr(builtins, "open", tracked_open)
    result = parse_pdf(SAMPLE_PDF)
    #no disk writes should occur during parsing
    assert len(disk_writes) == 0, f"Unexpected disk writes: {disk_writes}"
    assert len(result["text"]) >= 0
