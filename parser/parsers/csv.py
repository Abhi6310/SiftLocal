import io
import csv

def parse_csv(content: bytes) -> dict:
    #extract text and structure from CSV bytes
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    headers = rows[0] if rows else []
    row_count = len(rows)
    col_count = len(headers)
    return {
        "text": text,
        "metadata": {
            "file_type": "csv",
            "row_count": row_count,
            "column_count": col_count,
            "headers": headers,
            "char_count": len(text)
        }
    }
