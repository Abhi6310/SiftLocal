def parse_txt(content: bytes) -> dict:
    #extract text from TXT bytes
    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return {
        "text": text,
        "metadata": {
            "file_type": "txt",
            "line_count": len(lines),
            "char_count": len(text)
        }
    }
