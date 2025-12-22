import io
from pypdf import PdfReader

def parse_pdf(content: bytes) -> dict:
    #extract text from PDF bytes, return text and metadata
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    full_text = "\n\n".join(pages)
    return {
        "text": full_text,
        "metadata": {
            "file_type": "pdf",
            "page_count": len(reader.pages),
            "char_count": len(full_text)
        }
    }
