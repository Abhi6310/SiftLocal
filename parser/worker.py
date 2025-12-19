import sys
import json

#placeholders for now, add actual parsers later
def parse(content:bytes, file_type:str) -> dict:
    return {
        "text": "",
        "metadata": {"file_type": file_type, "size": len(content)}
    }

if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    content = input_data.get("content", "").encode()
    result = parse(content=content, file_type=input_data.get("file_type", "unknown"))
    print(json.dumps(result))
