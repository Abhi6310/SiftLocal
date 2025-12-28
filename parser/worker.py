import sys
import json
import base64
from parsers.pdf import parse_pdf
from parsers.pptx import parse_pptx

def parse(content: bytes, file_type: str) -> dict:
    #route to appropriate parser based on file type
    if file_type == ".pdf":
        return parse_pdf(content)
    elif file_type == ".pptx":
        return parse_pptx(content)
    #placeholder for other types
    return {
        "text": "",
        "metadata": {"file_type": file_type, "size": len(content)}
    }

if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    #content is base64-encoded for binary safety
    content = base64.b64decode(input_data.get("content", ""))
    file_type = input_data.get("file_type", "unknown")
    try:
        result = parse(content=content, file_type=file_type)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
